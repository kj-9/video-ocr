import json
from pathlib import Path

import click

from video_ocr import key_path
from video_ocr.playlist import Playlist


@click.group()
@click.version_option()
def cli():
    """"""


@cli.group()
def key():
    "Manage stored Youtube API key"


@key.command(name="path")
def key_path_command():
    "Output the path to the keys.json file"
    click.echo(key_path())


@key.command(name="set")
@click.argument("value", required=True, type=str)
def keys_set(value):
    """
    Save a key in the keys.json file
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
