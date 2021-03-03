from datetime import datetime
import os, time, sys, glob, re, hashlib, json

# local imports
from src.log import rootLogger
from src import config
from src import transform, deemix_api

logger = rootLogger.getChild('DOWNLOAD')

config = config.load()
download_commence = ''
downloaded_tracks = []

def get_md5(file):
    md5_hash = hashlib.md5()
    with open(file, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
        return md5_hash.hexdigest()


def return_download_commence():
    return download_commence


def validate_downloaded_tracks(downloaded_tracks):
    ret = {}

    for k in downloaded_tracks:
        track = downloaded_tracks[k]
        path = track["path"]
        if os.path.exists(path):
            ret[k] = {
                'irsc': k,
                'path': path,
                'md5': get_md5(path)
            }
    return ret


def missing_tracks():
    logger.info('Getting missing tracks to download')
    tracks = transform.get_tracks_to_download()

    logger.info(f'{len(tracks)} tracks pending download')

    if not tracks:
        logger.info('No tracks to download')
        return

    global download_commence
    download_commence = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    uris = {v['deezer_url'] for k, v in tracks.items()}
    deemix_api.download_url(uris)

    downloaded_tracks, failed_tracks = get_downloaded_track_paths(tracks)

    validated_tracks = validate_downloaded_tracks(downloaded_tracks)
    logger.info(f'Successfullu downloaded {len(validated_tracks)}/{len(uris)}')

    transform.set_tracks_as_downloaded(validated_tracks)
    transform.set_tracks_as_failed_to_download(failed_tracks)
    get_file_download_paths(validated_tracks)


def get_file_download_paths(tracks):
    global downloaded_tracks

    for k in tracks:
        downloaded_tracks.append(tracks[k]["path"])


def get_deemix_log_per_track(track, log_array):
    deezer_url = track["deezer_url"]
    deezer_id = track["deezer_id"]
    for i, line in enumerate(log_array):
        if f'Generating queue item for: {deezer_url}' in line:
            start_idx = i
        if str(deezer_id) in line and 'Finished downloading.' in line:
            end_idx = i+1
    track_log = log_array[start_idx:end_idx]

    return track_log


def parse_log_per_track(track, track_log_array):
    regex_mapping = {
        "Downloading the track": 1,
        "Track not available on deezer's servers!": 2,
        "Skipping track as it's already downloaded": 3
    }

    status_mapping = {
        1: "Completed successfully",
        2: "Failed to find track on Deezer (unavailable)",
        3: "Skipping, already downloaded"
    }

    status = None

    for i, line in enumerate(track_log_array):
        for k in regex_mapping:
            if k in line:
                status_code = regex_mapping[k]
                status = status_mapping[status_code]

    path = track_log_array[-2] if status_code == 1 or status_code == 3 else None

    ret = {
        'isrc': track["spotify_isrc"],
        'path': path,
        'status_code': status_code,
        'status': status
    }

    return ret


def get_downloaded_track_paths(missing_tracks):
    global download_commence

    log_file = os.path.join(config["deemix"]["config_path"], 'logs', f'{download_commence}.log')

    with open(log_file, mode='r', encoding='utf-8') as f:
        log_array = f.read().split("\n")

    ret = {}

    for k in missing_tracks:
        track = missing_tracks[k]

        attempted_track = parse_log_per_track(
            track,
            get_deemix_log_per_track(track, log_array)
        )

        ret[attempted_track["isrc"]] = attempted_track

    downloaded = {k: v for k, v in ret.items() if v["status_code"] != 2}
    failed = {k: v for k, v in ret.items() if v["status_code"] == 2}

    return downloaded, failed


def get_log_file_discrepancy(original_log_files, new_log_files):
    ret = []

    for log in new_log_files:
        if log not in original_log_files:
            ret.append(log)

    return ret


def get_log_files():
    return glob.glob(f'{os.path.join(config["deemix"]["config_path"], "logs")}/*')



"""
def download_track(song):
    logger.info(f'Downloading: {song["deezer_title"]} - {song["deezer_artist"]}')
    #commence = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    original_log_files = get_log_files()

    deemix_api.download_url([song['deezer_url']])

    new_log_files = get_log_files()

    potential_log_files = get_log_file_discrepancy(original_log_files, new_log_files)

    if len(potential_log_files) != 1:
        raise Exception("Expected one log file, got more")

    log_file = potential_log_files[0]

    download_path = get_download_path_new(log_file)

    downloaded_tracks.append(download_path)
    logger.info(f'Downloaded to: {download_path}')
    #remove_download_log(commence)


def missing_tracks_in_prog():
    logger.info('Getting missing tracks to download')
    tracks = transform.get_tracks_to_download()

    logger.info(f'{len(tracks)} missing tracks')

    if not tracks:
        logger.info('No tracks to download')
        return

    for i, k in enumerate(tracks):
        logger.info(f'{str(i+1)}/{str(len(tracks))}')
        download_track(tracks[k])

def get_download_path_new(log_file):
    ret = []

    with open(log_file, mode='r', encoding='utf-8') as f:
        log = f.read()
        lines = log.split('\n')
        slices = []

        for i, line in enumerate(lines):
            if 'Track download completed' in line:
                slices.append(i + 1)

        for i in slices:
            ret.append(lines[i])

    return ret


def get_download_path(commence):
    ret = []
    # Guess log file name
    try:
        log = os.path.join(config["deemix"]["config_path"], 'logs', f'{commence}.log')
        with open(log, mode='r', encoding='utf-8') as f:
            log = f.read()
            lines = log.split('\n')
            slices = []

            for i, line in enumerate(lines):
                if 'Track download completed' in line:
                    slices.append(i + 1)

            for i in slices:
                ret.append(lines[i])

        return ret
    except:
        logger.error(f'Failed opening {log}')
        raise Exception(f'Failed opening {log}')


def remove_download_log(commence):
    def remove_file(path):
        if os.path.isfile(path):
            os.remove(path)

    is_windows = (sys.platform == "win32")
    path = os.path.join(config["deemix"]["config_path"], 'logs', f'{commence}.log')

    if is_windows:
        logger.info('Its windows mofo!')
        try_fail_wait_repeat(3, remove_file(path))
    else:
        remove_file(path)


"""


