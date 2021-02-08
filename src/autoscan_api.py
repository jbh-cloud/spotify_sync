import requests
from pathlib import Path
import urllib

# local imports
from src import config
from src.log import rootLogger

logger = rootLogger.getChild('AUTOSCAN_API')

config = config.load()


def scan(paths):
    if config['autoscan']['enabled']:
        # get unique
        paths = list(set(paths))
        for p in paths:
            if Path(p).is_file():
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
                logger.debug(f'Plex scan request: {p}')
            else:
                logger.error(f'Failed to send Plex scan notification: {p}')
        logger.info(f'Processed {len(paths)} scan requests')