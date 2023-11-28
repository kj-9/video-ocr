import json
import os
from pathlib import Path


def get_key(explicit_key: str | None, env_var: str | None = None) -> str | None:
    """
    Return an API key based on a hierarchy of potential sources.

    :param explicit_key: A key provided by the user. This is an alias of a key in .video-ocr.json
    :param env_var: Name of the environment variable to check for the key.
    """
    stored_keys = load_keys()
    # If user specified an alias, use the key stored for that alias
    if explicit_key in stored_keys:
        return stored_keys[explicit_key]
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
