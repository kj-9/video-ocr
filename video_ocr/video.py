from dataclasses import dataclass
from pathlib import Path
from typing import NewType

import cv2
from config import DATA_DIR, get_logger
from playlist import Playlist
from pytube import YouTube
from serde import SerdeError, field, serde
from serde.json import from_json, to_json

from video_ocr.ocr import OCRResult, detect_text

logger = get_logger(__name__)
Frames = NewType("Frames", dict[Path, list[OCRResult]])


def frames_serializer(frames: Frames) -> dict[str, list]:
    """pyserde does not support dict keys to be `Path`, so we need to serialize/deserialize manually"""

    _frames = {str(k): v for k, v in frames.items()}
    return _frames


def frames_deserializer(_frames: dict[str, list]) -> Frames:
    frames = {Path(k): v for k, v in _frames.items()}

    return Frames(frames)


@serde
@dataclass
class Video:
    video_id: str
    video_path: Path = field(init=False)
    frames_dir: Path = field(init=False)
    # NOTE: ideally use `Frames` NewType but not currently supported by pyserde, see https://github.com/yukinarit/pyserde/issues/192
    frames: dict = field(
        default_factory=dict,
        serializer=frames_serializer,
        deserializer=frames_deserializer,
    )  # type Frames

    frame_rate: int = 100

    def __post_init__(self) -> None:
        data_dir = DATA_DIR / "videos" / self.video_id
        data_dir.mkdir(parents=True, exist_ok=True)

        self.video_path = data_dir / "video.mp4"
        self.frames_dir = data_dir / "frame"

        self.frames_dir.mkdir(parents=True, exist_ok=True)

    def download_video(self) -> None:
        yt = YouTube(f"https://www.youtube.com/watch?v={self.video_id}")
        logger.info(f"downloading video: {yt.title}")

        stream = yt.streams.filter(only_video=True).order_by("resolution").first()
        stream.download(
            output_path=self.video_path.parent, filename=self.video_path.name
        )

    @staticmethod
    def get_json_file(video_id: str) -> Path:
        return DATA_DIR / "videos" / video_id / "video.json"

    def to_frames(self, prefix: str = "frame-") -> tuple[Frames, int]:
        frames = Frames({})

        vid = cv2.VideoCapture(str(self.video_path))
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        index = 0

        logger.info("start converting image to frames...")
        while vid.isOpened():
            ret, frame = vid.read()

            # end of video
            if not ret:
                break

            if index % self.frame_rate == 0:
                frame_path = self.frames_dir / f"{prefix}{index}.png"

                cv2.imwrite(str(frame_path), frame)
                frames[frame_path] = []

            index += 1

        logger.info("finished converting image to frames.")
        vid.release()
        cv2.destroyAllWindows()

        self.frames = frames
        self.len_frames = len(frames)

        return self.frames, self.len_frames

    def get_frames_ocr(self) -> Frames:
        frames = self.frames

        logger.info("start OCR on frames...")
        for frame in frames.keys():
            res = detect_text(str(frame), languages=["ja"])

            if res:
                frames[frame] = res

        logger.info("completed OCR on frames.")
        self.frames = Frames(frames)

        return self.frames

    def to_json(self) -> Path:
        json_file = self.get_json_file(self.video_id)
        json_file.parent.mkdir(parents=True, exist_ok=True)

        s = to_json(self)
        with open(json_file, "w") as f:
            f.write(s)

        return json_file

    @classmethod
    def from_json(cls, video_id: str) -> "Video":
        json_file = cls.get_json_file(video_id)

        with open(json_file) as f:
            s = f.read()
        return from_json(cls, s)


RUN_OCR = True
if __name__ == "__main__":
    logger.info(Playlist.json_file)

    with open(Playlist.json_file) as f:
        s = f.read()
    playlist = from_json(Playlist, s)

    logger.info(len(playlist.items))

    video_ids = playlist.to_video_ids()
    len_video_ids = len(video_ids)

    logger.info(f"{len_video_ids=}")

    for i, video_id in enumerate(video_ids):
        logger.info(f"{(100*i) // len_video_ids}%, {video_id=}")

        try:
            video = Video.from_json(video_id)
        except SerdeError:
            video = Video(video_id)

        if not video.video_path.exists():
            video.download_video()

        if not video.frames:
            video.to_frames()

        logger.info(f"{video.to_json()=}")

        if RUN_OCR:  # and not any(video.frames.values()):
            video.get_frames_ocr()
            logger.info(f"{video.to_json()=}")
