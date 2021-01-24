import requests
from pathlib import Path

# local imports
import src.config as config


config = config.load()


def scan(paths):
    if config['autoscan']['enabled']:
        for p in paths:
            if config['autoscan']['scan_file_parent_path']:
                p = Path(p).parent
                #print(f'scan_file_parent_path is true, scanning parent: {p}')

            data = {
                'dir': p
            }

            if config['autoscan']['auth_enabled']:
                response = requests.post(config['autoscan']['endpoint'], data=data, auth=(
                    config['autoscan']['username'],
                    config['autoscan']['password'])
                )
            else:
                response = requests.post(config['autoscan']['endpoint'], data=data)

            if response.status_code == 200:
                print(f'PLex scan request: {p}')
            else:
                print(f'Failed to send Plex scan notification: {p}')