from datetime import datetime
import os

# local imports
from src.log import rootLogger
import src.config as config
from src.transform import get_tracks_to_download, set_tracks_as_downloaded
import src.deemix_api as deemix_api
from src.deemix_api import check_arl_valid

logger = rootLogger.getChild('DOWNLOAD')

config = config.load()
download_commence = ''
downloaded_tracks = []


def return_download_commence():
    return download_commence


def missing_tracks():
    logger.info('Getting missing tracks to download')
    tracks = get_tracks_to_download()

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
    set_tracks_as_downloaded(tracks)
    get_file_download_paths()


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


