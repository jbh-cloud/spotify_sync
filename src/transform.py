import src.config as config
from src.deezer_api import match_adv, match_isrc
import json, pathlib
from src.log import rootLogger

config = config.load()

logger = rootLogger.getChild('TRANSFORM')


def _verify_files():
    files = [config["script"]["paths"]["liked_songs"], config["script"]["paths"]["processed_songs"]]

    for f in files:
        if not pathlib.Path(f).is_file():
            logger.info(f'{f} not found, creating blank file')
            with open(f, mode='w', encoding='utf-8') as fp:
                json.dump({}, fp)


def process_liked():
    _verify_files()

    with open(config["script"]["paths"]["liked_songs"], mode='r', encoding='utf-8') as f:
        liked_songs = json.load(f)

    with open(config["script"]["paths"]["processed_songs"], mode='r', encoding='utf-8') as f:
        processed_songs = json.load(f)

    i = 1
    new_songs = 0
    matched_songs = 0

    logger.info('Starting match process')
    for k in liked_songs.keys():
        if k in processed_songs.keys():
            continue

        new_songs += 1
        song = liked_songs[k]

        logger.debug(f'Processing: {song["track"]["name"]} - {song["track"]["artists"][0]["name"]}')

        result = match_isrc(song)

        if result[0]:
            matched_songs += 1
            processed_songs[song['track']['external_ids']['isrc']] = result[1]
        else:
            logger.debug(f'Failed matching via {song["track"]["external_ids"]["isrc"]}, attempting fuzzy search')
            result = match_adv(song)
            if result[0]:
                logger.debug(f'Matched via fuzzy search')
                matched_songs += 1
                processed_songs[song['track']['external_ids']['isrc']] = result[1]
            else:
                logger.debug(f'Failed to match via fuzzy search, not matching..')
                processed_songs[song['track']['external_ids']['isrc']] = result[1]

        i += 1

    logger.info(f'Matched {matched_songs}/{new_songs} new liked songs')

    with open(config["script"]["paths"]["processed_songs"], mode='w', encoding='utf-8') as f:
        json.dump(processed_songs, f, indent=4, sort_keys=True)


def get_tracks_to_download():
    logger.debug(f'Opening {config["script"]["paths"]["processed_songs"]}')
    with open(config["script"]["paths"]["processed_songs"], mode='r', encoding='utf-8') as f:
        processed_songs = json.load(f)

    ret = {}
    for k in processed_songs.keys():
        if "match_pending_download" in processed_songs[k]:
            if processed_songs[k]["match_pending_download"]:
                logger.debug(f'{k} is matched and awaiting download')
                ret[k] = processed_songs[k].copy()

    return ret


def set_tracks_as_downloaded(tracks):
    with open(config["script"]["paths"]["processed_songs"], mode='r', encoding='utf-8') as f:
        processed_songs = json.load(f)

    for k in tracks:
        processed_songs[k]['match_pending_download'] = False
        processed_songs[k]['downloaded'] = True

    with open(config["script"]["paths"]["processed_songs"], mode='w', encoding='utf-8') as f:
        json.dump(processed_songs, f, indent=4, sort_keys=True)


