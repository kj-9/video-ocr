import os
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar
from serde import serde
from serde.json import to_json, from_json
import googleapiclient.discovery

from config import DATA_DIR, get_logger

logger = get_logger(__name__)


@dataclass
@serde
class Playlist:
    playlist_id: str = "UUcWWwmgV5dLmqUJCtAZqHfw"  # 中島浩二チャンネル
    items: list[dict] = None
    json_file: ClassVar[Path] = DATA_DIR / "playlist.json"

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
            logger.info(f"requesting playlist items...")
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
                logger.info(f"no more items. finish requesting playlist items.")
                break

        self.items = items
        return items

    def to_video_ids(self) -> list[str]:
        return list(map(lambda x: x.get("contentDetails").get("videoId"), self.items))


if __name__ == "__main__":
    playlist = Playlist()
    logger.info("fetching playlist items...")
    playlist.get_playlist()

    playlist.json_file.parent.mkdir(parents=True, exist_ok=True)
    s = to_json(playlist)

    logger.info("write playlist as json...")
    with open(playlist.json_file, "w") as f:
        f.write(s)

    logger.info("read written json...")
    with open(playlist.json_file, "r") as f:
        s = f.read()
    p2 = from_json(Playlist, s)

    logger.info("compare read playlist")
    print(playlist == p2)
