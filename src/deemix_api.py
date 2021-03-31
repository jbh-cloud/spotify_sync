import os, json
from deemix.app.cli import cli
import deezer as Deezer

# local imports
from src import config
from src import pushover_api
from src.log import rootLogger

from src.git_api import commit_files

config = config.load()
arl_valid = False
logger = rootLogger.getChild('DEEMIX_API')


def check_deemix_config():
    if not os.path.isdir(config["deemix"]["config_path"]):
        logger.error("config['deemix']['config_path'] must be an existing folder")
        raise Exception("config['deemix']['config_path'] must be an existing folder")
    if not os.path.isdir(config["deemix"]["download_path"]):
        logger.error(f'{config["deemix"]["download_path"]} must be an existing folder')
        raise Exception(f'{config["deemix"]["download_path"]} must be an existing folder')
    elif not os.path.isfile(os.path.join(config["deemix"]["config_path"], 'config.json')):
        if '\\' in config["deemix"]["download_path"]:
            config["deemix"]["download_path"] = config["deemix"]["download_path"].replace("\\", "/")
        config_json = json.loads(deemix_config.replace('DOWNLOAD_LOCATION_PATH', config["deemix"]["download_path"]))
        logger.info('Creating deemix config for first use')
        with open(os.path.join(config["deemix"]["config_path"], 'config.json'), mode='w', encoding='utf-8') as f:
            json.dump(config_json, f, indent=True)
        if config['git']['enabled']:
            # Ensure repo clean
            commit_files('Created deemix config for first use')


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


def download_url(url=[]):
    app = cli('', config['deemix']['config_path'])
    app.login()
    url = list(url)
    logger.info(f'Downloading {len(url)} songs from Deezer')
    app.downloadLink(url)


def download_file(path):
    print('Placeholder')



deemix_config = """
{
  "downloadLocation": "DOWNLOAD_LOCATION_PATH",
  "tracknameTemplate": "%artist% - %title%",
  "albumTracknameTemplate": "%artist% - %title%",
  "playlistTracknameTemplate": "%artist% - %title%",
  "createPlaylistFolder": false,
  "playlistNameTemplate": "%playlist%",
  "createArtistFolder": true,
  "artistNameTemplate": "%artist%",
  "createAlbumFolder": true,
  "albumNameTemplate": "%album%",
  "createCDFolder": false,
  "createStructurePlaylist": true,
  "createSingleFolder": true,
  "padTracks": true,
  "paddingSize": "0",
  "illegalCharacterReplacer": "_",
  "queueConcurrency": 10,
  "maxBitrate": "9",
  "fallbackBitrate": true,
  "fallbackSearch": false,
  "logErrors": true,
  "logSearched": false,
  "saveDownloadQueue": false,
  "overwriteFile": "n",
  "createM3U8File": false,
  "syncedLyrics": false,
  "embeddedArtworkSize": 1000,
  "localArtworkSize": 1400,
  "saveArtwork": false,
  "coverImageTemplate": "cover",
  "saveArtworkArtist": false,
  "artistImageTemplate": "folder",
  "PNGcovers": false,
  "jpegImageQuality": 80,
  "dateFormat": "Y-M-D",
  "removeAlbumVersion": false,
  "featuredToTitle": "0",
  "titleCasing": "nothing",
  "artistCasing": "nothing",
  "executeCommand": "",
  "tags": {
    "title": true,
    "artist": true,
    "album": true,
    "cover": true,
    "trackNumber": true,
    "trackTotal": false,
    "discNumber": true,
    "discTotal": false,
    "albumArtist": true,
    "genre": true,
    "year": true,
    "date": true,
    "explicit": false,
    "isrc": true,
    "length": true,
    "barcode": true,
    "bpm": true,
    "replayGain": false,
    "label": true,
    "lyrics": false,
    "copyright": false,
    "composer": true,
    "involvedPeople": false,
    "savePlaylistAsCompilation": false,
    "useNullSeparator": false,
    "saveID3v1": true,
    "multitagSeparator": "default",
    "syncedLyrics": false,
    "multiArtistSeparator": "default",
    "singleAlbumArtist": false,
    "coverDescriptionUTF8": false,
    "source": false
  },
  "playlistFilenameTemplate": "playlist",
  "embeddedArtworkPNG": false,
  "localArtworkFormat": "jpg",
  "albumVariousArtists": true,
  "removeDuplicateArtists": false,
  "tagsLanguage": ""
}
"""