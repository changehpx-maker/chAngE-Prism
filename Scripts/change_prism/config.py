import json
import os
import sys

_CONFIG_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.json")

_OS_DEFAULTS = {
    "server_root": "P:\\" if sys.platform == "win32" else "/Users/change_mac/Desktop/test",
    "local_projects_root": os.path.expanduser("~/Desktop/Projects"),
}


def load_config():
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _get_config_value(key):
    val = load_config().get(key, "")
    if val:
        return val
    return _OS_DEFAULTS.get(key, "")


def get_server_root():
    return _get_config_value("server_root")


def get_local_projects_root():
    return _get_config_value("local_projects_root")


def get_review_copy_destination_root():
    review_copy = load_config().get("review_copy", {})
    if not isinstance(review_copy, dict):
        return ""
    return review_copy.get("destination_root", "")


def get_config_path():
    return _CONFIG_PATH


def save_config_value(key, value):
    cfg = load_config()
    cfg[key] = value
    try:
        os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass
