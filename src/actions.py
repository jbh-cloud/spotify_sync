from src import spotify_, transform, download, pushover_, autoscan_, git_, deemix_, io_
from src.log import rootLogger

from datetime import datetime

logger = rootLogger.getChild('ACTIONS')


def auto():
    logger.info('Script started with -auto flag')

    # Checks
    deemix_.check_deemix_config()
    deemix_.check_arl_valid()

    pushover_.send_notification('Spotify downloader', 'Script started with --auto flag')
    git_.assert_repo()

    spotify_.download_liked()
    transform.process_liked()
    download.missing_tracks()
    autoscan_.scan(download.downloaded_song_paths)

    git_.commit_files(f'Spotify Downloader auto commit {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    if len(download.downloaded_song_paths) >= 1:
        pushover_.send_notification(
            'Spotify downloader',
            f'Successfully downloaded {len(download.downloaded_song_paths)} new songs(s)'
        )
    pushover_.send_notification('Spotify downloader', f'Script finished')
    logger.info('Script finished')


def sync_liked():
    logger.info('Script started with -sync-liked flag')
    spotify_.download_liked()
    logger.info('Script finished')


def sync_liked_custom_user(client_id, client_secret, username, liked_songs_path):
    logger.info('Script started with -download-liked flag')
    spotify_.download_liked_manual(client_id, client_secret, username, liked_songs_path)
    logger.info('Script finished')


def match_liked():
    logger.info('Script started with -match-liked flag')
    transform.process_liked()
    logger.info('Script finished')


def download_missing():
    logger.info('Script started with -download-missing flag')
    download.missing_tracks()
    logger.info('Script finished')


def authorize_spotify():
    spotify_.cache_spotify_auth()


def scan(paths):
    logger.info('Script started with -manual-scan flag')
    autoscan_.scan(paths)
    logger.info('Script finished')


def playlist_stats():
    logger.info('Script started with -playlist-stats flag')
    spotify_.display_playlist_stats()
    logger.info('Script finished')


def validate_downloaded_files():
    logger.info('Script started with -validate-downloaded-files flag')
    missing = io_.get_missing_files()
    logger.info(f'Found {str(missing)} missing songs')
    logger.info('Script finished')


def failed_download_stats():
    logger.info('Script started with -failed-download-stats flag')
    transform.display_failed_download_stats()
    logger.info('Script finished')