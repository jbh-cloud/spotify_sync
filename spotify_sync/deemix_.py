import sys
import os
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed, wait

# deemix
from deezer import Deezer
from deemix import generateDownloadObject
from deemix.downloader import Downloader
from deemix.utils import getBitrateNumberFromText
from deemix.types.DownloadObjects import Single

# local imports
from spotify_sync.config import Config
from spotify_sync.dataclasses import ProcessedSong, DownloadStatus
from spotify_sync.common import get_md5, dump_json, load_json

arl_valid = False


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
    def __init__(self, index: int, total: int, song: ProcessedSong, logger):
        self._logger = logger
        self._downloadIndex = index
        self._downloadTotal = total
        self._song = song
        self._base_message: str = ""
        self._get_base_message()

    def _get_base_message(self):
        if len(str(self._downloadIndex)) != len(str(self._downloadTotal)):
            zero_to_pad = len(str(self._downloadTotal)) - len(str(self._downloadIndex))
            self._base_message = f'{" ": <{zero_to_pad}}{str(self._downloadIndex)}/{str(self._downloadTotal)}'
        else:
            self._base_message = (
                f"{str(self._downloadIndex)}/{str(self._downloadTotal)}"
            )

    @staticmethod
    def _get_message(message):
        return f"- {message}" if message else ""

    def info(self, action: str, message: str):
        self._logger.info(
            f"{self._base_message} - {action} [{self._song.spotify_artist} - {self._song.spotify_title}] {self._get_message(message)}"
        )

    def warn(self, action: str, message: str):
        self._logger.warning(
            f"{self._base_message} - {action} [{self._song.spotify_artist} - {self._song.spotify_title}] {self._get_message(message)}"
        )

    def error(self, action: str, message: str):
        self._logger.error(
            f"{self._base_message} - {action} [{self._song.spotify_artist} - {self._song.spotify_title}] {self._get_message(message)}"
        )


class DeemixHelper:
    def __init__(self, app_config: Config):
        from spotify_sync.log import get_logger

        self._logger = get_logger().getChild("DeemixHelper")
        self.config = app_config

    def arl_valid(self) -> bool:
        self._logger.debug(f"Checking if arl is valid")
        global arl_valid
        if not arl_valid:
            self._logger.debug(f"arl_valid is False")
            arl = self.config.data["DEEMIX_ARL"].strip()
            self._logger.debug(f"Logging in with arl in config.json")
            client = Deezer()
            login = client.login_via_arl(arl)

            if login:
                self._logger.debug(f"Login successful")
                arl_valid = True
                return True
            else:
                self._logger.error(
                    f"Failed to login to Deezer with arl, you may need to refresh it"
                )
                return False

    def check_deemix_config(self):
        if os.path.isfile(self.config.data["DEEMIX_DOWNLOAD_PATH"]):
            self._logger.error(
                f'{self.config.data["DEEMIX_DOWNLOAD_PATH"]} is a file, must not exist or be an existent folder'
            )
            sys.exit(1)

        if not os.path.isdir(self.config.data["DEEMIX_DOWNLOAD_PATH"]):
            self._logger.warning(
                f'{self.config.data["DEEMIX_DOWNLOAD_PATH"]} does not exist, creating'
            )
            os.mkdir(self.config.data["DEEMIX_DOWNLOAD_PATH"])

        if "\\" in self.config.data["DEEMIX_DOWNLOAD_PATH"]:
            self.config.data["DEEMIX_DOWNLOAD_PATH"] = self.config.data[
                "DEEMIX_DOWNLOAD_PATH"
            ].replace("\\", "/")

        accepted_bitrates = ["lossless", "320", "360", "360_mq", "360_lq", "128"]
        if self.config.data["DEEMIX_MAX_BITRATE"] not in accepted_bitrates:
            self._logger.error(
                f'{self.config.data["DEEMIX_MAX_BITRATE"]} must be one of {",".join(accepted_bitrates)}'
            )
            sys.exit(1)

    def get_deemix_config(
        self,
    ) -> dict:
        deemix_config = DEFAULTS.copy()
        deemix_config["downloadLocation"] = self.config.data["DEEMIX_DOWNLOAD_PATH"]
        deemix_config["maxBitrate"] = getBitrateNumberFromText(
            self.config.data["DEEMIX_MAX_BITRATE"]
        )
        deemix_config["fallbackISRC"] = not self.config.data["DEEMIX_STRICT_MATCHING"]
        return deemix_config


class DeemixDownloader:
    def __init__(self, app_config: Config):
        from spotify_sync.log import get_logger

        self._logger = get_logger().getChild("DeemixDownloader")
        self.dz = Deezer()
        self.app_config = app_config
        self.config = DeemixHelper(self.app_config).get_deemix_config()
        self.deezer_logged_in = self.dz.login_via_arl(
            self.app_config.data["DEEMIX_ARL"]
        )
        self.skip_low_quality = self.app_config.data["DEEMIX_SKIP_LOW_QUALITY"]
        self.max_bitrate = self.app_config.data["DEEMIX_MAX_BITRATE"]
        self.songs_to_download: List[ProcessedSong] = []
        self.download_report: Dict[str, DownloadStatus] = {}

    def download_wrapper(self, index, num_urls_to_download, song, download_obj):
        logger = DownloadLogger(
            index=index, total=num_urls_to_download, song=song, logger=self._logger
        )
        listener = LogListener()
        dl = Downloader(self.dz, download_obj, self.config, listener)

        logger.info(action="STARTING", message="")
        dl.start()

        self.update_download_report(dl.downloadObject, song, listener, logger)

    def download_songs(self, songs: List[ProcessedSong]):
        self.songs_to_download = songs

        if not self.deezer_logged_in:
            self._logger.error("Failed to login with arl, you may need to refresh it")
            sys.exit(1)

        if self.skip_low_quality and self.max_bitrate in ["lossless", "320"]:
            if self.max_bitrate == "lossless" and not self.dz.current_user.get(
                "can_stream_lossless"
            ):
                self._logger.info(
                    f"SKIP_LOW_QUALITY is specified and unable to stream FLAC, stopping script! "
                    f"If this is unexpected, please ensure your Deezer account is Premium/Hi-Fi"
                )
                sys.exit(1)

            if self.max_bitrate == "320" and not self.dz.current_user.get(
                "can_stream_hq"
            ):
                self._logger.info(
                    f"SKIP_LOW_QUALITY is specified and unable to stream 320, stopping script1 "
                    f"If this is unexpected, please ensure your Deezer account is Premium/Hi-Fi"
                )
                sys.exit(1)

        self._logger.info(f"Gathering song information in preparation for download..")
        download_objs = []
        with ThreadPoolExecutor(self.app_config.data["THREADS"]) as executor:
            dl_obj_futures = {
                executor.submit(
                    generateDownloadObject,
                    self.dz,
                    v.deezer_url,
                    self.config["maxBitrate"],
                ): v
                for v in self.songs_to_download
            }
            for future in as_completed(dl_obj_futures):
                song = dl_obj_futures[future]
                download_obj = future.result()
                download_objs.append({"song": song, "download_obj": download_obj})

        num_urls_to_download = len(self.songs_to_download)
        with ThreadPoolExecutor(self.app_config.data["THREADS"]) as executor:
            dl_futures = [
                executor.submit(
                    self.download_wrapper,
                    i + 1,
                    num_urls_to_download,
                    v["song"],
                    v["download_obj"],
                )
                for i, v in enumerate(download_objs)
            ]
            wait(dl_futures)

    @staticmethod
    def download_skipped(listener: LogListener):
        download_skipped = False
        for m in listener.messages:
            if "downloadInfo" in m:
                if m["downloadInfo"].get("state") == "alreadyDownloaded":
                    download_skipped = True

        return download_skipped

    def update_download_report(
        self,
        download_object,
        requested_song: ProcessedSong,
        listener: LogListener,
        dl_logger,
    ):
        if not isinstance(download_object, Single):
            self._logger.error("Not a Single, unexpected type!", type(download_object))
            sys.exit(1)

        errors = None
        md5 = ""
        status = False
        f = ""
        downloaded_isrc = None
        downloaded_link = None
        downloaded_id = None
        download_skipped = self.download_skipped(listener)

        if download_object.downloaded == 1:
            downloaded_isrc = download_object.single["trackAPI"]["isrc"]
            downloaded_link = download_object.single["trackAPI"]["link"]
            downloaded_id = download_object.single["trackAPI"]["id"]
            f = download_object.files[0]["path"]

            if download_skipped:
                dl_logger.info(
                    action="FINSIHED", message=f"Skipping, already downloaded"
                )
                status = True
                md5 = get_md5(f)

            elif os.path.isfile(f):
                dl_logger.info(action="FINSIHED", message=f"Successfully downloaded")
                status = True
                md5 = get_md5(f)
            else:
                dl_logger.warn(
                    action="FINSIHED",
                    message=f"Failed, downloaded but could not find {f}",
                )
                errors = [f"Downloaded but could not find {f}"]

        elif download_object.failed == 1:
            dl_logger.warn(
                action="FINSIHED",
                message=f'Failed, download for DeezerId: {download_object.single["trackAPI"]["id"]} error: {download_object.errors[0]["message"]}',
            )
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

    def get_report(self) -> Tuple[int, int, List[DownloadStatus]]:
        count_of_failed = 0
        count_of_succeeded = 0
        reports = []

        for v in self.download_report.values():
            if not v.success:
                count_of_failed += 1
            else:
                count_of_succeeded += 1

            reports.append(v)

        return count_of_failed, count_of_succeeded, reports

    @staticmethod
    def extract_isrc_from_download_object(obj):
        return obj.single["trackAPI"]["isrc"]


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
    "maxBitrate": "9",  # default to lossless
    "feelingLucky": False,
    "fallbackBitrate": True,  # Allow lower quality than target
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
        "coverDescriptionUTF8": False,
    },
}
