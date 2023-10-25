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
    playlist_id: str
    items: list[dict] = field(default_factory=list)

    @staticmethod
    def get_json_file() -> Path:
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

    def first_video_id_item(self, video_id):
        for item in self.items:
            if item.get("contentDetails").get("videoId") == video_id:
                return item

    def to_video_ids(self) -> list[str]:
        return list(map(lambda x: x.get("contentDetails").get("videoId"), self.items))  # type: ignore

    def to_json(self) -> Path:
        json_file = self.get_json_file()

        json_file.parent.mkdir(parents=True, exist_ok=True)
        s = to_json(self, indent=4)

        with open(json_file, "w") as f:
            f.write(s)

        return json_file

    @classmethod
    def from_json(cls) -> "Playlist":
        json_file = cls.get_json_file()

        with open(json_file) as f:
            s = f.read()

        return from_json(cls, s)


if __name__ == "__main__":
    playlist = Playlist()
    logger.info("fetching playlist items...")
    playlist.get_playlist()

    logger.info("write playlist as json...")
    json_file = playlist.to_json()

    p2 = Playlist.from_json()

    logger.info("compare read playlist")
    print(playlist == p2)
