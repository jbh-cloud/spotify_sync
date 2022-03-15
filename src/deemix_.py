from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from typing import List, Dict
from dataclasses import dataclass
import psutil

# deemix
from deezer import Deezer
from deemix import generateDownloadObject
from deemix.downloader import Downloader
from deemix.utils import getBitrateNumberFromText
from deemix.types.DownloadObjects import Single

# local imports
from src.config import load as load_config
from src import pushover_
from src.log import rootLogger
from src.transform import ProcessedSong

config = load_config()
arl_valid = False
logger = rootLogger.getChild('DEEMIX')


# bitrate_name_to_number = {
#     '360': 15,
#     '360_mq': 14,
#     '360_lq': 13,
#     'lossless': 9,
#     '320': 3,
#     '128': 1
# }


class LogListener:
    def __init__(self):
        self.messages = []

    def send(self, key, value=None):
        self.messages.append({key: value})


class DownloadLogger:
    def __init__(self, index: int, total: int, song: ProcessedSong):
        self._logger = logger
        self._downloadIndex = index
        self._downloadTotal = total
        self._song = song
        self._base_message: str = ""
        self._get_base_message()

    def _get_base_message(self):
        if len(str(self._downloadIndex)) != len(str(self._downloadTotal)):
            zero_to_pad = len(str(self._downloadTotal)) - len(str(self._downloadIndex))
            self._base_message = f'{"0": <{zero_to_pad}}{str(self._downloadIndex)}/{str(self._downloadTotal)}'
        else:
            self._base_message = f'{str(self._downloadIndex)}/{str(self._downloadTotal)}'

    @staticmethod
    def _get_message(message):
        return f"- {message}" if message else ''

    def info(self, action: str, message: str):
        self._logger.info(f'{self._base_message} - {action} [{self._song.spotify_artist} - {self._song.spotify_title}] {self._get_message(message)}')

    def warn(self, action: str, message: str):
        self._logger.warning(
            f'{self._base_message} - {action} [{self._song.spotify_artist} - {self._song.spotify_title}] {self._get_message(message)}')

    def error(self, action: str, message: str):
        self._logger.error(
            f'{self._base_message} - {action} [{self._song.spotify_artist} - {self._song.spotify_title}] {self._get_message(message)}')


@dataclass
class DownloadStatus:
    spotify_id: str
    deezer_id: str
    requested_isrc: str
    downloaded_isrc: str
    requested_url: str
    downloaded_url: str
    requested_bitrate: str
    downloaded_bitrate: str
    success: bool
    skipped: bool
    errors: List[str]
    download_path: str
    md5: str


class DeemixDownloader:
    def __init__(self, arl: str, config: dict, skip_low_quality=False):
        self.dz = Deezer()
        self.config = config
        self.deezer_logged_in = self.dz.login_via_arl(arl)
        self.skip_low_quality = skip_low_quality
        self.songs_to_download: List[ProcessedSong] = []
        self.download_report: Dict[str, DownloadStatus] = {}

    def download_wrapper(self, data):
        index = data['index'] + 1
        num_urls_to_download = data['num_urls_to_download']
        song = data['song']
        download_obj = data['download_obj']

        logger = DownloadLogger(index=index, total=num_urls_to_download, song=song)
        listener = LogListener()
        dl = Downloader(self.dz, download_obj, self.config, listener)

        logger.info(action='STARTING', message='')
        dl.start()

        self.update_download_report(dl.downloadObject, song, listener, logger)

    def download_songs(self, songs: List[ProcessedSong]):
        self.songs_to_download = songs

        if self.skip_low_quality and not self.dz.current_user.get('can_stream_lossless'):
            logger.info(f'SKIP_LOW_QUALITY is specified and unable to stream FLAC, stopping download')
            logger.info(f'If this is unexpected, please ensure your Deezer account is Premium/Hi-Fi')
            raise Exception()

        if not self.deezer_logged_in:
            raise Exception('Failed to login with arl, you may need to refresh it')

        logger.info(f'Gathering song information in preparation for download..')
        download_objs = {v.spotify_id: {'song': v, 'download_obj': generateDownloadObject(self.dz, v.deezer_url, self.config['maxBitrate'])} for v in self.songs_to_download}
        threads = get_threads()

        num_urls_to_download = len(self.songs_to_download)
        with ThreadPoolExecutor(threads) as executor:
            for i, k in enumerate(download_objs):
                v = download_objs[k]
                executor.submit(self.download_wrapper, {
                    'index': i,
                    'num_urls_to_download': num_urls_to_download,
                    'song': v['song'],
                    'download_obj': v['download_obj']
                })

    @staticmethod
    def download_skipped(listener: LogListener):
        download_skipped = False
        for m in listener.messages:
            if 'downloadInfo' in m:
                if m['downloadInfo'].get('state') == 'alreadyDownloaded':
                    download_skipped = True

        return download_skipped

    def update_download_report(self, download_object, requested_song: ProcessedSong, listener: LogListener, dl_logger):
        if not isinstance(download_object, Single):
            raise Exception("Not a Single, unexpected type!", download_object)
        errors = None
        md5 = ""
        status = False
        f = ""
        downloaded_isrc = None
        downloaded_link = None
        downloaded_id = None

        if download_object.downloaded == 1:
            downloaded_isrc = download_object.single['trackAPI']['isrc']
            downloaded_link = download_object.single['trackAPI']['link']
            downloaded_id = download_object.single['trackAPI']['id']
            download_skipped = self.download_skipped(listener)
            f = download_object.files[0]['path']

            if download_skipped:
                dl_logger.info(action='FINSIHED', message=f'Skipping, already downloaded')
                status = True
                md5 = get_md5(f)

            elif os.path.isfile(f):
                dl_logger.info(action='FINSIHED', message=f'Successfully downloaded')
                status = True
                md5 = get_md5(f)
            else:
                dl_logger.warn(action='FINSIHED', message=f'Failed, downloaded but could not find {f}')
                errors = [f"Downloaded but could not find {f}"]

        elif download_object.failed == 1:
            dl_logger.warn(action='FINSIHED', message=f'Failed, download for DeezerId: {download_object.single["trackAPI"]["id"]} error: {download_object.errors[0]["message"]}')
            errors = download_object.errors

        self.download_report[requested_song.spotify_id] = DownloadStatus(
            spotify_id=requested_song.spotify_id,
            deezer_id=downloaded_id,
            requested_isrc=requested_song.deezer_isrc,
            downloaded_isrc=downloaded_isrc,
            requested_url=requested_song.deezer_url,
            downloaded_url=downloaded_link,
            requested_bitrate=self.config["maxBitrate"],
            downloaded_bitrate=download_object.bitrate,
            success=status,
            skipped=download_skipped,
            errors=errors or [],
            download_path=f,
            md5=md5,
        )

    def get_report(self):
        count_of_failed = 0
        count_of_succeeded = 0
        reports = {}

        for v in self.download_report.values():
            if not v.success:
                count_of_failed += 1
            else:
                count_of_succeeded += 1

            reports[v.spotify_id] = v

        return count_of_failed, count_of_succeeded, reports

    @staticmethod
    def extract_isrc_from_download_object(obj):
        return obj.single["trackAPI"]["isrc"]


def get_threads():
    machine_threads = psutil.cpu_count()
    if config["THREADS"] == "":
        return machine_threads

    try:
        threads = int(config["THREADS"])
        threads = threads if int(config["THREADS"]) <= machine_threads else machine_threads
    except:
        threads = machine_threads
        logger.warning(f'THREADING - Failed parsing int from "{config["THREADS"]}", using max available ({str(machine_threads)})')

    return threads


def get_md5(file):
    md5_hash = hashlib.md5()
    with open(file, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
        return md5_hash.hexdigest()


def check_deemix_config():
    if os.path.isfile(config["DEEMIX_DOWNLOAD_PATH"]):
        logger.error(f'{config["DEEMIX_DOWNLOAD_PATH"]} is a file, must not exist or be an existent folder')
        raise

    if not os.path.isdir(config["DEEMIX_DOWNLOAD_PATH"]):
        logger.warning(f'{config["DEEMIX_DOWNLOAD_PATH"]} does not exist, creating')
        os.mkdir(config["DEEMIX_DOWNLOAD_PATH"])

    if '\\' in config["DEEMIX_DOWNLOAD_PATH"]:
        config["DEEMIX_DOWNLOAD_PATH"] = config["DEEMIX_DOWNLOAD_PATH"].replace("\\", "/")

    accepted_bitrates = ['lossless', '320', '360', '360_mq', '360_lq', '128']
    if config["DEEMIX_MAX_BITRATE"] not in accepted_bitrates:
        logger.error(f'{config["DEEMIX_MAX_BITRATE"]} must be one of {",".join(accepted_bitrates)}')


def check_arl_valid():
    logger.debug(f'Checking if arl is valid')
    global arl_valid
    if not arl_valid:
        logger.debug(f'arl_valid is False')
        arl = config["DEEMIX_ARL"].strip()
        logger.debug(f'Logging in with arl in config.json')
        client = Deezer()
        login = client.login_via_arl(arl)

        if login:
            logger.debug(f'Login successful')
            arl_valid = True
        else:
            logger.error(f'Login unsuccessful, raising exception')
            pushover_.send_notification('Spotify downloader', 'Failed to validate arl')
            raise Exception('Failed to login with arl, you may need to refresh it')


def get_deemix_config():
    deemix_config = DEFAULTS.copy()
    deemix_config["downloadLocation"] = config["DEEMIX_DOWNLOAD_PATH"]
    deemix_config["maxBitrate"] = getBitrateNumberFromText(config["DEEMIX_MAX_BITRATE"])
    deemix_config["fallbackISRC"] = not config["DEEMIX_STRICT_MATCHING"]
    return deemix_config


DEFAULTS = {
  "downloadLocation": "DOWNLOAD_LOCATION_PATH",
  "tracknameTemplate": "%artist% - %title%",
  "albumTracknameTemplate": "%artist% - %title%",
  "playlistTracknameTemplate": "%position% - %artist% - %title%",
  "createPlaylistFolder": False,
  "playlistNameTemplate": "%playlist%",
  "createArtistFolder": True,
  "artistNameTemplate": "%artist%",
  "createAlbumFolder": True,
  "albumNameTemplate": "%album%",
  "createCDFolder": False,
  "createStructurePlaylist": True,
  "createSingleFolder": True,
  "padTracks": True,
  "paddingSize": "0",
  "illegalCharacterReplacer": "_",
  "maxBitrate": "9", # default to lossless
  "feelingLucky": False,
  "fallbackBitrate": False,
  "fallbackSearch": False,
  "fallbackISRC": True,
  "featuredToTitle": True,
  "logErrors": True,
  "logSearched": False,
  "overwriteFile": False,
  "createM3U8File": False,
  "playlistFilenameTemplate": "playlist",
  "syncedLyrics": False,
  "embeddedArtworkSize": 800,
  "embeddedArtworkPNG": False,
  "localArtworkSize": 1400,
  "localArtworkFormat": "jpg",
  "saveArtwork": False,
  "coverImageTemplate": "cover",
  "saveArtworkArtist": False,
  "artistImageTemplate": "folder",
  "jpegImageQuality": 90,
  "dateFormat": "Y-M-D",
  "albumVariousArtists": True,
  "removeAlbumVersion": False,
  "removeDuplicateArtists": True,
  "titleCasing": "nothing",
  "artistCasing": "nothing",
  "executeCommand": "",
  "tags": {
    "title": True,
    "artist": True,
    "artists": True,
    "album": True,
    "cover": True,
    "trackNumber": True,
    "trackTotal": False,
    "discNumber": True,
    "discTotal": False,
    "albumArtist": True,
    "genre": True,
    "year": True,
    "date": True,
    "explicit": False,
    "isrc": True,
    "length": True,
    "barcode": False,
    "bpm": True,
    "replayGain": False,
    "label": True,
    "lyrics": False,
    "syncedLyrics": False,
    "copyright": False,
    "composer": False,
    "involvedPeople": False,
    "source": False,
    "rating": False,
    "savePlaylistAsCompilation": False,
    "useNullSeparator": False,
    "saveID3v1": True,
    "multiArtistSeparator": "default",
    "singleAlbumArtist": False,
    "coverDescriptionUTF8": False
  }
}