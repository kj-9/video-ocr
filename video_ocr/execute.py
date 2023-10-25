import timeit
import typing as t
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from time import monotonic

from serde import SerdeError

from video_ocr.config import get_logger
from video_ocr.video import Video

logger = get_logger(__name__)


def _load_or_create_video(video_id: str, load=False) -> Video:
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
        logger.info(f"{video.video_path=} does not exist, downloading video...")
        video.download_video()

    return video


def _to_frames_if_not_exists(video: Video) -> None:
    if not video.frames:
        video.to_frames()
        logger.info(f"{video.to_json()=}")


def func_to_frames_if_not_exists(load=True) -> t.Callable:
    def closure(video_id: str):
        video = _load_or_create_video(video_id, load=load)
        _to_frames_if_not_exists(video)

    return closure


def _run_ocr_if_not_exists(video: Video) -> None:
    results = [frame.results for frame in video.frames]

    if any(results):
        logger.info(f"{video.video_id=} has already saved results, stop ocr.")
        # already saved results
        return

    logger.info(f"{video.video_id=} has no saved results, run ocr.")
    video.get_frames_ocr()
    logger.info(f"{video.to_json()=}")


def func_run_ocr_if_not_exists() -> t.Callable:
    def closure(video_id: str):
        video = _load_or_create_video(
            video_id, load=True
        )  # must load video with frames
        _run_ocr_if_not_exists(video)

    return closure


def run_on_thread_pool(exec_func, *iterable, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return executor.map(exec_func, *iterable)


def run_on_process_pool(exec_func, *iterable, max_workers=None):
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        executor.map(exec_func, *iterable)


def log_time(function):
    def wrap(*args, **kwargs):
        start_time = monotonic()
        function_return = function(*args, **kwargs)
        logger.info(f"{function.__name__}:Run time {monotonic() - start_time} seconds")
        return function_return

    return wrap


def run_ocr_multi_process(video_ids: list[str], load=False) -> None:
    logger.info("start saving frames.")
    run_on_thread_pool(func_to_frames_if_not_exists(load), video_ids)
    logger.info("finish saving frames.")

    logger.info("start saving ocr results.")
    # must load=True, since we need to load generated frames
    # or there will be no frames to ocr
    run_on_process_pool(func_run_ocr_if_not_exists(), video_ids)
    logger.info("finish saving ocr results.")


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
