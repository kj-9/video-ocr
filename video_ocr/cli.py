import json
from pathlib import Path

import click

import video_ocr as vo
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
def keys_set(value):
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


@cli.command(name="playlist")
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


@cli.group()
def video():
    "Manage videos"


@video.command(name="run")
@click.argument("video_id", required=True, type=str)
@click.option(
    "--output-dir",
    "-od",
    default=".",
    type=click.Path(file_okay=False, writable=True),
)
@click.option(
    "--frame-rate",
    "-fr",
    default=100,
    type=int,
    help="Number of frames per second to extract from the video",
)
@click.option(
    "--resolution",
    "--res",
    default="worst",
    type=click.Choice(["worst", "best"]),
    help="Resolution of the video to download",
)
def write_video(video_id, output_dir, frame_rate, resolution):
    """Write a video to a json file"""
    vo.config.DATA_DIR = Path(output_dir)
    video = Video(video_id, frame_rate=frame_rate)
    video.download_video(resolution=resolution)
    video.to_frames()
    video.get_frames_ocr()
    video.to_json()


@video.command(name="resolutions")
@click.argument("video_id", required=True, type=str)
def get_resolutions(video_id):
    """Get resolutions for a video"""
    video = Video(video_id)
    resolutions = video.get_resolutions()
    for resolution in resolutions:
        click.echo(resolution)
