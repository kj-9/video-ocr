import json
from pathlib import Path

import click

from video_ocr import key_path
from video_ocr.playlist import Playlist
from video_ocr.video import Video


@click.group()
@click.version_option()
def cli():
    """"""


@cli.group()
def key():
    "Manage stored Youtube API key"


@key.command(name="path")
def key_path_command():
    "Output the path to the .video-ocr.json file"
    click.echo(key_path())


@key.command(name="set")
@click.argument("value", required=True, type=str)
def key_set(value):
    """
    Save a key in the .video-ocr.json file
    """
    default = {"// Note": "This file stores secret API credentials. Do not share!"}
    path = key_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(default))
    try:
        current = json.loads(path.read_text())
    except json.decoder.JSONDecodeError:
        current = default
    current["YOUTUBE_API_KEY"] = value
    path.write_text(json.dumps(current, indent=2) + "\n")


@cli.group()
def youtube():
    "Manage Youtube resources"


@youtube.command(name="playlist")
@click.argument("playlist_id", required=True, type=str)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=True, writable=True, dir_okay=False, allow_dash=True),
)
def write_playlist(playlist_id, output):
    """Write a playlist to a json file"""
    if not output:
        output_path = Path(f"{playlist_id}.json")

        counter = 1
        while output_path.exists():
            # update suffix with -{counter}.json
            output_path = Path(f"{playlist_id}.{counter}.json")
            counter += 1

    else:
        output_path = Path(output)

    playlist = Playlist(playlist_id)
    playlist.get_playlist()

    playlist.to_json(output_path)


@youtube.command(name="ls")
@click.argument("video_id", required=True, type=str)
def get_resolutions(video_id):
    """Get resolutions for a video"""
    resolutions = Video.get_resolutions(video_id)
    for resolution in resolutions:
        click.echo(resolution)


@youtube.command(name="download")
@click.argument("video_id", required=True, type=str)
@click.option(
    "--output",
    "-o",
    required=True,
)
@click.option(
    "--resolution",
    "--res",
    default="worst",
    type=str,
    help="Resolution of the video to download. worst/best or a itag. Use `video-ocr video resolutions` to get a list of itags",
)
def download_video(video_id, output, resolution):
    """Download a video"""
    video = Video(video_file=Path(output))
    video.download_video(video_id, resolution=resolution)


@cli.command(name="run")
@click.argument(
    "video_file", required=True, type=click.Path(dir_okay=False, writable=True)
)
@click.option(
    "--output",
    "-o",
    default="./output.json",
    type=click.Path(dir_okay=False, writable=True),
    help="Directory to store output",
)
@click.option(
    "--frames-dir",
    "-fd",
    default="./.frames",
    type=click.Path(file_okay=False, writable=True),
    help="Directory to store frames",
)
@click.option(
    "--frame-rate",
    "-fr",
    default=100,
    type=int,
    help="Number of frames per second to extract from the video",
)
def run_ocr(video_file, output, frames_dir, frame_rate):
    """Write a ocr json file from a video file"""

    video = Video(
        output_file=Path(output),
        video_file=Path(video_file),
        frames_dir=Path(frames_dir),
        frame_rate=frame_rate,
    )
    video.gen_frame_files()
    video.run_ocr()
    video.to_json()
