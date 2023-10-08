import timeit
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from time import monotonic

from serde import SerdeError

from video_ocr.config import get_logger
from video_ocr.playlist import Playlist
from video_ocr.video import Video

logger = get_logger(__name__)


def load_or_create_video(video_id: str, load=False) -> Video:
    if load:
        try:
            video = Video.from_json(video_id)
        except SerdeError as e:
            logger.warning(
                f"{video_id=}: failed to load Video from json, creating fresh Video instance"
            )
            logger.error(e)
            video = Video(video_id)
        except FileNotFoundError as e:
            logger.warning(
                f"{video_id=}: file is not found, creating fresh Video instance"
            )
            logger.error(e)
            video = Video(video_id)

    else:
        video = Video(video_id)

    if not video.video_path.exists():
        video.download_video()

    return video


def save_frames(video):
    if not video.frames:
        video.to_frames()
        logger.info(f"{video.to_json()=}")


def save_ocr_results(video):
    results = [frame.results for frame in video.frames]

    if any(results):
        # already saved results
        return

    video.get_frames_ocr()
    logger.info(f"{video.to_json()=}")


# excecution time comparison
def execute_save_frames(video_id, load=True):
    save_frames(load_or_create_video(video_id, load=load))


def execute_save_results(video_id, load=True):
    save_ocr_results(load_or_create_video(video_id, load=load))


def run_on_thread_pool(exec_func, iterable, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(exec_func, iterable)


def run_on_process_pool(exec_func, iterable, max_workers=None):
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        executor.map(exec_func, iterable)


def log_time(function):
    def wrap(*args, **kwargs):
        start_time = monotonic()
        function_return = function(*args, **kwargs)
        logger.info(f"{function.__name__}:Run time {monotonic() - start_time} seconds")
        return function_return

    return wrap


def check_performance(
    video_ids: list[str],
    exec_func,
    pattern=None,
    tp_max_worker=4,
    mp_max_worker=None,
) -> dict[str, float | dict]:
    """
    for 10 videos,
    - gen_frames
        - sync: 30.243480375000217
        - async:
            - 20.119083291001516, for 4 workers
            - 22.35446845899969 , for 10 workers
        - multi proc: 23.37792808300037

    - ocr
        - sync: 47.840016333000676
        - async: 40.077069167000445
        - multi proc: 27.40532650000023
    """

    if pattern is None:
        pattern = ["sync", "async", "multi-proc"]
    result: dict[str, dict | float] = {"args": locals()}

    if "sync" in pattern:
        start = timeit.default_timer()
        for video_id in video_ids:
            exec_func(video_id, load=False)

        end = timeit.default_timer()
        logger.info(f"sync: {end - start}")
        result["sync"] = end - start

    if "async" in pattern:
        start = timeit.default_timer()
        run_on_thread_pool(exec_func, video_ids, False, max_workers=tp_max_worker)
        end = timeit.default_timer()
        logger.info(f"async: {end - start}")
        result["sync"] = end - start

    if "multi-proc" in pattern:
        start = timeit.default_timer()
        run_on_process_pool(exec_func, video_ids, False, max_workers=mp_max_worker)
        end = timeit.default_timer()
        logger.info(f"multi proc: {end - start}")
        result["sync"] = end - start

    return result


CHECK_PERFORMANCE = False
if __name__ == "__main__":
    playlist = Playlist.from_json(Playlist.json_file)

    logger.info(len(playlist.items))

    video_ids = playlist.to_video_ids()
    len_video_ids = len(video_ids)

    logger.info(f"{len_video_ids=}")

    start = timeit.default_timer()
    run_on_thread_pool(execute_save_frames, video_ids)
    end = timeit.default_timer()
    logger.info(f"finish save frames: {end - start}")

    start = timeit.default_timer()
    run_on_process_pool(execute_save_results, video_ids)
    end = timeit.default_timer()
    logger.info(f"finish save ocr results: {end - start}")

    if CHECK_PERFORMANCE:
        # sampling
        sample_video_ids = video_ids[:10]
        # choose task
        logger.info(f"{check_performance(sample_video_ids, execute_save_frames)=}")
        logger.info(f"{check_performance(sample_video_ids, execute_save_results)=}")
