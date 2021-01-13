from deemix.app.cli import cli
import src.config as config
import json

config = config.load()

def download_url(url=[]):
    configFolder = config['deemix']['config_path']
    app = cli('', configFolder)
    app.login()
    url = list(url)
    app.downloadLink(url)

def download_file(path):
    print('Placeholder')


#download_url(['https://www.deezer.com/track/104515176'])

