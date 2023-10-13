import os
from dataclasses import dataclass, field
from pathlib import Path

import googleapiclient.discovery
from serde import serde
from serde.json import from_json, to_json

import video_ocr as vo
from video_ocr.config import get_logger

logger = get_logger(__name__)


@dataclass
@serde
class Playlist:
    items: list[dict] = field(default_factory=list)
    playlist_id: str = "UUcWWwmgV5dLmqUJCtAZqHfw"  # 中島浩二チャンネル

    @classmethod
    def json_file(self) -> Path:
        return vo.config.DATA_DIR / "playlist.json"

    def __get_api(self) -> googleapiclient.discovery.Resource:
        DEVELOPER_KEY = os.environ.get("YOUTUBE_API_KEY")

        if not DEVELOPER_KEY:
            raise Exception("YOUTUBE_API_KEY is not set")

        api_service_name = "youtube"
        api_version = "v3"

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=DEVELOPER_KEY
        )

        return youtube

    def get_playlist(self, max_results: int = 500) -> list[dict]:
        youtube = self.__get_api()
        next_page_token = None

        items = []

        while True:
            logger.info("requesting playlist items...")
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=self.playlist_id,
                maxResults=max_results,
                pageToken=next_page_token,
            )
            response = request.execute()

            items.extend(response["items"])

            next_page_token = response.get("nextPageToken")

            if not next_page_token:
                logger.info("no more items. finish requesting playlist items.")
                break

        self.items = items
        return items

    def to_video_ids(self) -> list[str]:
        return list(map(lambda x: x.get("contentDetails").get("videoId"), self.items))  # type: ignore

    @classmethod
    def from_json(cls, json_file: Path) -> "Playlist":
        with open(json_file) as f:
            s = f.read()
        return from_json(cls, s)


if __name__ == "__main__":
    playlist = Playlist()
    logger.info("fetching playlist items...")
    playlist.get_playlist()

    json_file = playlist.json_file()
    json_file.parent.mkdir(parents=True, exist_ok=True)
    s = to_json(playlist)

    logger.info("write playlist as json...")
    with open(json_file, "w") as f:
        f.write(s)

    logger.info("read written json...")
    with open(json_file) as f:
        s = f.read()
    p2 = from_json(Playlist, s)

    logger.info("compare read playlist")
    print(playlist == p2)
