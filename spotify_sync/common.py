import json
import subprocess
import sys
from typing import Any, Dict
import hashlib
import tempfile
from pathlib import Path
import uuid

# local imports
from spotify_sync.dataclasses import SpotifySong, ProcessedSong


def as_spotify_song(songs: dict) -> Dict[str, SpotifySong]:
    ret = {}
    for k in songs:
        s = SpotifySong()
        s.from_dict(songs[k])
        ret[k] = s

    return ret


def as_processed_song(songs: dict) -> Dict[str, ProcessedSong]:
    ret = {}
    for k in songs:
        ret[k] = ProcessedSong(**songs[k])

    return ret


def get_md5(file):
    md5_hash = hashlib.md5()
    with open(file, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
        return md5_hash.hexdigest()


def get_temp_dir() -> Path:
    dir_ = Path(tempfile.gettempdir())
    dir_.mkdir(exist_ok=True)
    return dir_


def get_temp_fn(extension=".txt") -> str:
    return str(uuid.uuid4()) + extension


def get_temp_file(extension=".txt") -> Path:
    temp_dir = get_temp_dir()
    return temp_dir / (str(uuid.uuid4()) + extension)


def load_json(file: Path) -> dict:
    if file.is_file():
        with open(file, mode="r", encoding="utf-8") as f:
            ret = json.load(f)
    else:
        ret = {}

    return ret


def dump_json(file: Path, data: Any, hidden=False, sort_keys=True) -> None:
    def obj_dict(obj):
        return obj.__dict__

    if hidden and file.exists():
        set_hidden_attribute(file, mode="unhide")

    with open(file, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, sort_keys=sort_keys, default=obj_dict)

    if hidden:
        set_hidden_attribute(file, mode="hide")


def set_hidden_attribute(file: Path, mode: str):
    assert mode in ["hide", "unhide"]
    if sys.platform.startswith("win32") and mode == "hide":
        subprocess.check_call(["attrib", "+H", file])
    elif sys.platform.startswith("win32") and mode == "unhide":
        subprocess.check_call(["attrib", "-H", file])
