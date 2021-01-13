#from deemix.__main__ import download
from deemix.app.cli import cli
from pathlib import Path
import os

def download(url):
    localpath = Path('.')
    #configFolder = '../config'
    configFolder = 'D:\\source\\spotify_download\\config'
    print(f'Config folder is {os.path.abspath(configFolder)}')
    #if path is not None:
    #    if path == '': path = '.'
    #    path = Path(path)
    #    print(f'Setting output path to {os.path.abspath(path)}')

    print('Initalizing app')
    app = cli('', configFolder)
    print('Authenicating to Deezer')
    app.login()
    url = list(url)

    try:
        isfile = Path(url[0]).is_file()
    except:
        isfile = False
    if isfile:
        filename = url[0]
        with open(filename) as f:
            url = f.readlines()

    app.downloadLink(url)



#download(url, bitrate, portable, path)
#(url, bitrate, portable, path)
#download(['https://www.deezer.com/track/1160380192'], 'flac', 'D:\\deemix_music')
download(['https://www.deezer.com/track/1160380192','https://www.deezer.com/album/103115532'])




