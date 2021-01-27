import src.spotify_api as spotify_api
import src.transform as transform
import src.banner as banner
import src.download as download
import src.pushover_api as pushover_api
import src.autoscan_api as autoscan_api
import src.git_api as git_api
from src.log import rootLogger

logger = rootLogger.getChild('ACTIONS')


def auto():
    logger.info('Script started with auto flag')
    pushover_api.send_notification('Spotify downloader', 'Script started with --auto flag')
    download.check_arl_valid()
    git_api.assert_repo()

    spotify_api.download_liked()
    transform.process_liked()
    download.missing_tracks()
    autoscan_api.scan(download.downloaded_tracks)

    git_api.commit_files()

    if len(download.downloaded_tracks) >= 1:
        pushover_api.send_notification(
            'Spotify downloader',
            f'Successfully downloaded {len(download.downloaded_tracks)} new tracks'
        )
    pushover_api.send_notification('Spotify downloader', f'Script finished')
    logger.info('Script finished')


def sync_liked():
    logger.info('Script started with download-liked flag')
    spotify_api.download_liked()
    logger.info('Script finished')


def sync_liked_custom_user(client_id, client_secret, username, liked_songs_path):
    logger.info('Script started with download-liked flag')
    spotify_api.download_liked_manual(client_id, client_secret, username, liked_songs_path)
    logger.info('Script finished')


def match_liked():
    logger.info('Script started with process-liked flag')
    transform.process_liked()
    logger.info('Script finished')


def download_missing():
    logger.info('Script started with download-missing flag')
    download.missing_tracks()
    logger.info('Script finished')


def authorize_spotify():
    spotify_api.cache_spotify_auth()


def scan(paths):
    logger.info('Script started with manual-scan flag')
    autoscan_api.scan(paths)
    logger.info('Script finished')