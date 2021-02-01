from datetime import datetime
import os, time, sys

# local imports
from src.log import rootLogger
from src import config
from src import transform, deemix_api

logger = rootLogger.getChild('DOWNLOAD')

config = config.load()
download_commence = ''
downloaded_tracks = []


def return_download_commence():
    return download_commence


def missing_tracks():
    logger.info('Getting missing tracks to download')
    tracks = transform.get_tracks_to_download()

    logger.info(f'{len(tracks)} missing tracks')

    if not tracks:
        logger.info('No tracks to download')
        return

    uris = []
    for k in tracks:
        uris.append(tracks[k]['deezer_url'])

    global download_commence
    download_commence = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    deemix_api.download_url(uris)
    transform.set_tracks_as_downloaded(tracks)
    get_file_download_paths()


def download_track(song):
    logger.info(f'Downloading: {song["deezer_title"]} - {song["deezer_artist"]}')
    commence = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    deemix_api.download_url([song['deezer_url']])
    download_path = get_download_path(commence)
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

    for k in tracks:
        download_track(tracks[k])


def get_file_download_paths():
    global download_commence
    global downloaded_tracks
    # Guess log file name
    try:
        log = os.path.join(config["deemix"]["config_path"], 'logs', f'{download_commence}.log')
        with open(log, mode='r', encoding='utf-8') as f:
            log = f.read()
            lines = log.split('\n')
            slices = []

            for i, line in enumerate(lines):
                if 'Track download completed' in line:
                    slices.append(i + 1)

            for i in slices:
                downloaded_tracks.append(lines[i])

    except:
        logger.error(f'Failed opening {log}')
        raise Exception(f'Failed opening {log}')


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


def try_fail_wait_repeat(maximum_number_of_tries, func, *args):
    """A dirty solution for a dirty bug in windows python2"""
    i = 0
    while True:
        try:
            res = func(*list(args))
            return res
        except WindowsError as e:
            i += 1
            time.sleep(1)
            if i > maximum_number_of_tries:
                logger.error("Too much trying to run {}({})".format(func, args))
                raise e

