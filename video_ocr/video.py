from dataclasses import dataclass
from pathlib import Path
from typing import NewType

import cv2
from config import DATA_DIR, get_logger
from pytube import YouTube
from serde import field, serde
from serde.json import from_json, to_json

from video_ocr.ocr import OCRResult, detect_text

logger = get_logger(__name__)
Frames = NewType("Frames", dict[Path, list[OCRResult]])


@serde
@dataclass
class Frame:
    path: Path
    results: list[OCRResult]


@serde
@dataclass
class Video:
    video_id: str
    video_path: Path = field(init=False)
    frames_dir: Path = field(init=False)
    # NOTE: ideally use `Frames` NewType but not currently supported by pyserde, see https://github.com/yukinarit/pyserde/issues/192
    frames: list[Frame] = field(default_factory=list)  # type Frames

    frame_rate: int = 100

    def __post_init__(self) -> None:
        data_dir = DATA_DIR / "videos" / self.video_id
        data_dir.mkdir(parents=True, exist_ok=True)

        self.video_path = data_dir / "video.mp4"
        self.frames_dir = data_dir / "frame"

        self.frames_dir.mkdir(parents=True, exist_ok=True)

        # validation
        if self.frames:
            frame_paths = [str(frame.path) for frame in self.frames]

            if len(frame_paths) != len(set(frame_paths)):
                raise ValueError("frame paths must be unique.")

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

    def to_frames(self, prefix: str = "frame-") -> tuple[list[Frame], int]:
        frames = []

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
                frames.append(Frame(path=frame_path, results=[]))

            index += 1

        logger.info("finished converting image to frames.")
        vid.release()
        cv2.destroyAllWindows()

        self.frames = frames
        self.len_frames = len(frames)

        return self.frames, self.len_frames

    def get_frames_ocr(self) -> list[Frame]:
        frames = self.frames

        logger.info("start OCR on frames...")
        for i, frame in enumerate(frames):
            results = detect_text(str(frame.path), languages=["ja"])

            if results:
                frame.results = results
                frames[i] = frame

        logger.info("completed OCR on frames.")
        self.frames = frames

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
