import src.config as config
from src.transform import get_tracks_to_download, set_tracks_as_downloaded
import src.deemix_api as deemix_api
from datetime import datetime
import os


config = config.load()
download_commence = ''
downloaded_tracks = []


def return_download_commence():
    return download_commence


def missing_tracks():
    tracks = get_tracks_to_download()

    if not tracks:
        print('No tracks to download')
        return

    print(f'Downloading missing tracks')

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
        with open(os.path.join(config["deemix"]["config_path"], 'logs', f'{download_commence}.log'), mode='r', encoding='utf-8') as f:
            log = f.read()
            lines = log.split('\n')
            slices = []

            for i, line in enumerate(lines):
                if 'Track download completed' in line:
                    slices.append(i + 1)

            for i in slices:
                downloaded_tracks.append(lines[i])

    except:
        raise Exception('Failed opening file')


