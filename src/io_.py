import json
import os
import pathlib

# local imports
from src.config import load as load_config
from src.log import rootLogger
from src.functions import ensure_directory

logger = rootLogger.getChild('IO')
config = load_config()


def verify_files():
    files = [config["DATA_FILES_LIKED_SONGS"], config["DATA_FILES_PROCESSED_SONGS"]]

    for f in files:
        f = os.path.join(config["DATA_PERSISTENT_DATA_ROOT"], f)
        if not pathlib.Path(f).is_file():
            with open(f, mode='w', encoding='utf-8') as fp:
                json.dump({}, fp)


def load_liked_songs():
    file = os.path.join(config["DATA_PERSISTENT_DATA_ROOT"], config["DATA_FILES_LIKED_SONGS"])
    return load_json(file)


def load_processed_songs():
    file = os.path.join(config["DATA_PERSISTENT_DATA_ROOT"], config["DATA_FILES_PROCESSED_SONGS"])
    return load_json(file)


def load_json(file):
    if os.path.isfile(file):
        with open(file, mode='r', encoding='utf-8') as f:
            ret = json.load(f)
    else:
        ret = {}

    return ret


def dump_json(file, obj):
    def obj_dict(obj):
        return obj.__dict__

    with open(file, mode='w', encoding='utf-8') as f:
        json.dump(obj, f, indent=4, sort_keys=True, default=obj_dict)


def persist_processed_songs(songs):
    file = os.path.join(config["DATA_PERSISTENT_DATA_ROOT"], config["DATA_FILES_PROCESSED_SONGS"])
    ensure_directory(file)
    dump_json(file, songs)


def persist_liked_songs(songs):
    file = os.path.join(config["DATA_PERSISTENT_DATA_ROOT"], config["DATA_FILES_LIKED_SONGS"])
    ensure_directory(file)
    dump_json(file, songs)


def get_missing_files():
    f = os.path.join(config["DATA_PERSISTENT_DATA_ROOT"], config["DATA_FILES_PROCESSED_SONGS"])
    with open(f, mode='r', encoding='utf-8-sig') as f:
        processed_songs = json.load(f)

    missing = 0
    for path in [v['download_path'] for k, v in processed_songs.items() if v['downloaded']]:
        if not os.path.isfile(path):
            print(f'[MISSING] - {path}')
            missing += 1

    return missing