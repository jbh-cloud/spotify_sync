import src.config as config
from src.transform import get_tracks_to_download, set_tracks_as_downloaded
import src.deemix_api as deemix_api

config = config.load()


def missing_tracks():
    tracks = get_tracks_to_download()

    if not tracks:
        print('No tracks to download')
        return

    print(f'Downloading missing tracks')

    uris = []
    for k in tracks:
        uris.append(tracks[k]['deezer_url'])

    deemix_api.download_url(uris)
    set_tracks_as_downloaded(tracks)

