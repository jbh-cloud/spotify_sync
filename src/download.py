from typing import List

# local imports
from src.deemix_ import DownloadStatus, get_deemix_config
from src.log import rootLogger
from src.config import load as load_config
from src import transform, deemix_

logger = rootLogger.getChild('DOWNLOAD')

config = load_config()
downloaded_song_paths = []


def missing_tracks():
    logger.info('Getting missing tracks to download')
    songs = transform.get_songs_to_download()

    logger.info(f'{len(songs)} tracks pending download')
    if not songs:
        logger.info('No tracks to download')
        return

    logger.info(f'Downloading {len(songs)} song(s) from Deezer')
    downloader = deemix_.DeemixDownloader(
        arl=config["DEEMIX_ARL"], config=get_deemix_config(), skip_low_quality=config['DEEMIX_SKIP_LOW_QUALITY'])
    downloader.download_songs(songs)
    failed_songs, succeeded_songs, reports = downloader.get_report()
    logger.info(f'Successfully downloaded {succeeded_songs}/{len(songs)}')

    transform.persist_download_status(reports)
    get_file_download_paths(reports)


def get_file_download_paths(download_report: List[DownloadStatus]):
    global downloaded_song_paths

    for k in download_report:
        if download_report[k].success:
            downloaded_song_paths.append(download_report[k].download_path)


