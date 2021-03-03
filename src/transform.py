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


def load_json(file):
    with open(file, mode='r', encoding='utf-8') as f:
        ret = json.load(f)
    return ret


def dump_json(file, obj):
    with open(file, mode='w', encoding='utf-8') as f:
        json.dump(obj, f, indent=4, sort_keys=True)


def get_unprocessed_songs(spotify_songs, processed_songs):
    ret = {}
    for k in spotify_songs:
        if k not in processed_songs:
            ret[k] = spotify_songs[k]
    return ret


def insert_into_processed(match_obj, processed_songs):
    processed_song = {
            'spotify_title': match_obj['spotify_title'],
            'spotify_artist': match_obj['spotify_artist'],
            'spotify_isrc': match_obj['spotify_isrc'],
            'spotify_url': match_obj['spotify_url'],
            'spotify_id': match_obj['spotify_id'],
            'deezer_title': match_obj['deezer_title'],
            'deezer_artist': match_obj['deezer_artist'],
            'deezer_url': match_obj['deezer_url'],
            'deezer_id': match_obj['deezer_id'],
            'matched': match_obj['matched'],
            'match_type': match_obj['match_type'],
            'match_pending_download': match_obj['match_pending_download'],
            'downloaded': match_obj['downloaded'],
            'download_path': None,
            'download_md5': None,
            'download_failed': None,
            'download_failed_reason': None
    }
    processed_songs[match_obj["spotify_isrc"]] = processed_song


def match_unprocessed(unprocessed_songs, processed_songs):
    logger.info(f'Attempting to match {len(unprocessed_songs)} Spotify songs to Deezer')

    matched = 0
    for k in unprocessed_songs:
        song = unprocessed_songs[k]

        logger.debug(f'Processing: {song["track"]["name"]} - {song["track"]["artists"][0]["name"]}')

        result = match_isrc(song)

        if result[0]:
            insert_into_processed(result[1], processed_songs)
            matched += 1
        else:
            logger.debug(f'Failed matching via {song["track"]["external_ids"]["isrc"]}, attempting fuzzy search')
            result = match_adv(song)
            if result[0]:
                logger.debug(f'Matched via fuzzy search')
                insert_into_processed(result[1], processed_songs)
                matched += 1
            else:
                logger.debug(f'Failed to match via fuzzy search, not matching..')
                insert_into_processed(result[1], processed_songs)

    logger.info(f'Matched {matched}/{len(unprocessed_songs)} new liked songs')


def process_liked():
    _verify_files()

    liked_songs = load_json(config["script"]["paths"]["liked_songs"])
    processed_songs = load_json(config["script"]["paths"]["processed_songs"])

    unprocessed_songs = get_unprocessed_songs(liked_songs, processed_songs)
    logger.info(f'{len(unprocessed_songs)} new songs to process')

    match_unprocessed(unprocessed_songs, processed_songs)

    dump_json(config["script"]["paths"]["processed_songs"], processed_songs)


def get_tracks_to_download():
    logger.debug(f'Opening {config["script"]["paths"]["processed_songs"]}')
    processed_songs = load_json(config["script"]["paths"]["processed_songs"])

    ret = {}
    for k in processed_songs.keys():
        if "match_pending_download" in processed_songs[k]:
            if "download_failed" in processed_songs[k]:
                if processed_songs[k]["match_pending_download"] and not processed_songs[k]["download_failed"]:
                    logger.debug(f'{k} is matched and awaiting download')
                    ret[k] = processed_songs[k].copy()
            else:
                if processed_songs[k]["match_pending_download"]:
                    logger.debug(f'{k} is matched and awaiting download')
                    ret[k] = processed_songs[k].copy()
    return ret


def set_tracks_as_downloaded(tracks):
    processed_songs = load_json(config["script"]["paths"]["processed_songs"])

    for k in tracks:
        processed_songs[k]['match_pending_download'] = False
        processed_songs[k]['downloaded'] = True
        processed_songs[k]['download_path'] = tracks[k]['path']
        processed_songs[k]['download_md5'] = tracks[k]['md5']
        processed_songs[k]['download_failed'] = False
        processed_songs[k]['download_failed_reason'] = None

    dump_json(config["script"]["paths"]["processed_songs"], processed_songs)


def set_tracks_as_failed_to_download(failed_tracks):
    processed_songs = load_json(config["script"]["paths"]["processed_songs"])

    for k in failed_tracks:
        processed_songs[k]['match_pending_download'] = True
        processed_songs[k]['downloaded'] = False
        processed_songs[k]['download_path'] = None
        processed_songs[k]['download_md5'] = None
        processed_songs[k]['download_failed'] = True
        processed_songs[k]['download_failed_reason'] = failed_tracks[k]["status"]

    dump_json(config["script"]["paths"]["processed_songs"], processed_songs)