import json
import os
from pathlib import Path

import click


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


def get_key(
    explicit_key: str | None, key_alias: str, env_var: str | None = None
) -> str | None:
    """
    Return an API key based on a hierarchy of potential sources.

    :param provided_key: A key provided by the user. This may be the key, or an alias of a key in keys.json.
    :param key_alias: The alias used to retrieve the key from the keys.json file.
    :param env_var: Name of the environment variable to check for the key.
    """
    stored_keys = load_keys()
    # If user specified an alias, use the key stored for that alias
    if explicit_key in stored_keys:
        return stored_keys[explicit_key]
    if explicit_key:
        # User specified a key that's not an alias, use that
        return explicit_key
    # Stored key over-rides environment variables over-ride the default key
    if key_alias in stored_keys:
        return stored_keys[key_alias]
    # Finally try environment variable
    if env_var and os.environ.get(env_var):
        return os.environ[env_var]
    # Couldn't find it
    return None


def load_keys():
    path = key_path()
    if path.exists():
        return json.loads(path.read_text())
    else:
        return {}


def key_path():
    return user_dir() / ".video-ocr.json"


def user_dir():
    video_ocr_user_path = os.environ.get("VIDEO_OCR_USER_PATH")
    if video_ocr_user_path:
        path = Path(video_ocr_user_path)
    else:
        path = Path.home()

    path.mkdir(exist_ok=True, parents=True)
    return path


@cli.command(name="command")
@click.argument("example")
@click.option(
    "-o",
    "--option",
    help="An example option",
)
def first_command(example, option):
    "Command description goes here"
    click.echo("Here is some output")
