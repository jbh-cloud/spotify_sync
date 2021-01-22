from deemix.app.cli import cli
import deezer as Deezer
import json

# local imports
import src.config as config
import src.pushover_api as pushover_api


config = config.load()
arl_valid = False

def download_url(url=[]):
    app = cli('', config['deemix']['config_path'])
    app.login()
    url = list(url)
    app.downloadLink(url)


def download_file(path):
    print('Placeholder')


def check_arl_valid():
    global arl_valid
    if not arl_valid:
        arl = config['deemix']['arl'].strip()
        client = Deezer.Deezer()
        login = client.login_via_arl(arl)

        if login:
            with open(config['deemix']['config_path'] / '.arl', 'w') as f:
                f.write(arl)
            arl_valid = True
        else:
            pushover_api.send_notification('Spotify downloader', 'Failed to validate arl')
            raise Exception('Failed to login with arl, you may need to refresh it')


#download_url(['https://www.deezer.com/track/104515176'])
check_arl_valid()

