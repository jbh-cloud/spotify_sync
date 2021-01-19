import requests
import src.config as config


config = config.load()


def scan(paths):
    if config['plex_autoscan']['enabled']:
        for p in paths:
            url = config['plex_autoscan']['uri']
            data = {
                'eventType': 'Manual',
                'filepath': p
                #'filepath': config['plex_autoscan']['deemix_media_path']
                #'filepath': '/mnt/unionfs/Media/Spotify/liked'
            }

            response = requests.post(config['plex_autoscan']['uri'], data=data)
            if response.status_code == 200:
                print(f'PLex scan request: {p}')
            else:
                print(f'Failed to send Plex scan notification: {p}')

