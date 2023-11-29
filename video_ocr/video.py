from dataclasses import dataclass
from pathlib import Path

import cv2
from pytube import YouTube
from serde import field, serde
from serde.json import from_json, to_json

import video_ocr as vo
from video_ocr.config import get_logger
from video_ocr.ocr import OCRResult, detect_text

logger = get_logger(__name__)


@serde
@dataclass
class Frame:
    file_name: str
    results: list[OCRResult]


@serde
@dataclass
class Video:
    video_id: str
    frame_rate: int = 100
    frames: list[Frame] = field(default_factory=list)

    # internals
    video_path: Path = field(init=False, skip=True)
    frames_dir: Path = field(init=False, skip=True)

    def __post_init__(self) -> None:
        data_dir = vo.config.DATA_DIR / "videos" / self.video_id
        data_dir.mkdir(parents=True, exist_ok=True)

        self.video_path = data_dir / "video.mp4"
        self.frames_dir = data_dir / "frame"

        self.frames_dir.mkdir(parents=True, exist_ok=True)

        # validation
        if self.frames:
            frame_paths = self.frame_paths

            if len(frame_paths) != len(set(frame_paths)):
                raise ValueError("frame paths must be unique.")

    def get_resolutions(self) -> list:
        yt = YouTube(f"https://www.youtube.com/watch?v={self.video_id}")
        streams = yt.streams.filter(only_video=True)
        return list(streams)

    def download_video(self, resolution="worst") -> None:
        yt = YouTube(f"https://www.youtube.com/watch?v={self.video_id}")
        logger.info(f"downloading video: {yt.title}")

        streams = yt.streams.filter(only_video=True)

        if resolution == "worst":
            stream = streams.order_by("resolution").first()
        elif resolution == "best":
            stream = streams.order_by("resolution").last()

        stream.download(
            output_path=self.video_path.parent, filename=self.video_path.name
        )

    @staticmethod
    def get_json_file(video_id: str) -> Path:
        return vo.config.DATA_DIR / "videos" / video_id / "video.json"

    @property
    def frame_paths(self) -> list[Path]:
        return [self.frames_dir / frame.file_name for frame in self.frames]

    def to_frames(self, prefix: str = "frame-") -> tuple[list[Frame], int]:
        frames = []

        vid = cv2.VideoCapture(str(self.video_path))
        index = 0

        logger.info("start converting image to frames...")
        while vid.isOpened():
            ret, frame = vid.read()

            # end of video
            if not ret:
                break

            if index % self.frame_rate == 0:
                file_name = f"{prefix}{index}.png"
                frame_path = self.frames_dir / file_name

                cv2.imwrite(str(frame_path), frame)
                frames.append(Frame(file_name=file_name, results=[]))

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
        for i, frame_path in enumerate(self.frame_paths):
            results = detect_text(str(frame_path), languages=["ja"])

            if results:
                frames[i].results = results

        logger.info("completed OCR on frames.")
        self.frames = frames

        return self.frames

    def to_json(self) -> Path:
        json_file = self.get_json_file(self.video_id)
        json_file.parent.mkdir(parents=True, exist_ok=True)

        s = to_json(self, indent=4)
        with open(json_file, "w") as f:
            f.write(s)

        return json_file

    @classmethod
    def from_json(cls, video_id: str) -> "Video":
        json_file = cls.get_json_file(video_id)

        with open(json_file) as f:
            s = f.read()
        return from_json(cls, s)
