import requests
from pathlib import Path
import urllib

# local imports
import src.config as config


config = config.load()


def scan(paths):
    if config['autoscan']['enabled']:
        for p in paths:
            if config['autoscan']['scan_file_parent_path']:
                p = Path(p).parent

            params = {'dir': p}

            if config['autoscan']['auth_enabled']:
                response = requests.post(config['autoscan']['endpoint'], params=params, auth=(
                    config['autoscan']['username'],
                    config['autoscan']['password'])
                )
            else:
                response = requests.post(config['autoscan']['endpoint'], params=params)

            if response.status_code == 200:
                print(f'Plex scan request: {p}')
            else:
                print(f'Failed to send Plex scan notification: {p}')