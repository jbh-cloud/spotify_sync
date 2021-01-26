from deemix.app.cli import cli
import deezer as Deezer
import os
import logging


# local imports
import src.config as config
import src.pushover_api as pushover_api
from src.log import rootLogger


config = config.load()
arl_valid = False
logger = rootLogger.getChild('DEEMIX_API')


def download_url(url=[]):
    app = cli('', config['deemix']['config_path'])
    app.login()
    url = list(url)
    logger.info(f'Downloading {url}')
    app.downloadLink(url)


def download_file(path):
    print('Placeholder')


def check_arl_valid():
    logger.debug(f'Checking if arl is valid')
    global arl_valid
    if not arl_valid:
        logger.debug(f'arl_valid is False')
        arl = config['deemix']['arl'].strip()
        logger.debug(f'Logging in with arl in config.json')
        client = Deezer.Deezer()
        login = client.login_via_arl(arl)

        if login:
            logger.debug(f'Login successful, caching token locally')
            with open(os.path.join(config['deemix']['config_path'], '.arl'), 'w') as f:
                f.write(arl)
                arl_valid = True
        else:
            logger.error(f'Login unsuccessful, raising exception')
            pushover_api.send_notification('Spotify downloader', 'Failed to validate arl')
            raise Exception('Failed to login with arl, you may need to refresh it')


check_arl_valid()

#download_url(['https://testurl.com'])