from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
from config import DATA_DIR, get_logger
from ocrmac import ocrmac
from playlist import Playlist
from pytube import YouTube
from serde import serde
from serde.json import from_json, to_json

logger = get_logger(__name__)


@dataclass
@serde
class Video:
    video_id: str
    video_path: Path = field(init=False)
    frames_dir: Path = field(init=False)
    frames: list[Path] = field(default_factory=list)
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

    def to_frames(self, prefix: str = "frame-") -> tuple[list[Path], int]:
        frames = []

        vid = cv2.VideoCapture(str(self.video_path))
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        index = 0

        while vid.isOpened():
            ret, frame = vid.read()

            # end of video
            if not ret:
                break

            if index % self.frame_rate == 0:
                logger.info(f"frame: {index}")
                frame_path = self.frames_dir / f"{prefix}{index}.png"

                cv2.imwrite(str(frame_path), frame)
                frames.append(frame_path)

            index += 1

        vid.release()
        cv2.destroyAllWindows()

        self.frames = frames
        self.len_frames = len(frames)

        return self.frames, self.len_frames

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
        return from_json(Video, s)


def read_text_macos(frame: Path, lang: Optional[list] = None) -> str:
    if lang is None:
        lang = ["ja"]
    return ocrmac.OCR(str(frame), language_preference=lang).recognize()


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
        video = Video(video_id)

        if not video.video_path.exists():
            video.download_video()

        logger.info(f"{video.to_json()=}")
