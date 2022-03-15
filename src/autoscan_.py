import requests
from pathlib import Path

# local imports
from src.config import load as load_config
from src.log import rootLogger

logger = rootLogger.getChild('AUTOSCAN')

config = load_config()


def scan(paths):
    if config["AUTOSCAN_ENABLED"]:
        unique = set()
        for p in paths:
            if Path(p).is_file():
                p = Path(p).parent
            unique.add(p)

        for p in unique:
            params = {'dir': p}

            if config["AUTOSCAN_AUTH_ENABLED"]:
                response = requests.post(config["AUTOSCAN_ENDPOINT"], params=params, auth=(
                    config["AUTOSCAN_USERNAME"],
                    config["AUTOSCAN_PASSWORD"])
                )
            else:
                response = requests.post(config["AUTOSCAN_ENDPOINT"], params=params)

            if response.status_code == 200:
                logger.debug(f'Plex scan request: {p}')
            else:
                logger.error(f'Failed to send Plex scan notification: {p}')
        logger.info(f'Processed {len(paths)} scan request(s)')