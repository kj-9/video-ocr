from video_ocr.video import Video
from video_ocr.playlist import Playlist
from video_ocr.config import get_logger
from serde import SerdeError

logger = get_logger(__name__)


def load_or_create_video(video_id: str, load=False) -> Video:

    if load:
        try:
            video = Video.from_json(video_id)
        except SerdeError:
            logger.warn('failed to load Video from json, creating fresh Video instance')
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

    video.get_frames_ocr()
    logger.info(f"{video.to_json()=}")



# excecution time comparison
def execute_save_frames(video_id):
    save_frames(load_or_create_video(video_id, load=False))


def execute_save_results(video_id):
    save_ocr_results(load_or_create_video(video_id, load=True))




if __name__ == "__main__":
    playlist = Playlist.from_json(Playlist.json_file)

    logger.info(len(playlist.items))

    video_ids = playlist.to_video_ids()
    len_video_ids = len(video_ids)

    logger.info(f"{len_video_ids=}")

    from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
    import timeit

    video_ids = video_ids[:10]
    execute = execute_save_results # execute_save_frames

    # sync
    start = timeit.default_timer()
    for i, video_id in enumerate(video_ids):
        execute(video_id)

    end = timeit.default_timer()
    logger.info(f"sync: {end - start}")
    # frames: sync: 30.243480375000217, for 10 videos
    # ocr: sync: 47.840016333000676


    # async
    start = timeit.default_timer()
    videos = []
    with ThreadPoolExecutor(max_workers=4) as e:

        for i, video_id in enumerate(video_ids):
            videos.append(e.submit(execute , video_id))

    end = timeit.default_timer()
    logger.info(f"async: {end - start}")
    # frames: async: 20.119083291001516, for 10 videos, 4 workers
    # ocr async: 40.077069167000445

    # process pool
    print(video_ids)
    start = timeit.default_timer()
    with ProcessPoolExecutor() as executor:
            
            executor.map(execute, video_ids)



    end = timeit.default_timer()
    logger.info(f"multi proc: {end - start}")
    # frames: multi proc: 23.37792808300037
    # ocr: multi proc: 27.40532650000023
