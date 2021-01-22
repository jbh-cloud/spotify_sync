import src.spotify_api as spotify_api
import src.transform as transform
import src.banner as banner
import src.download as download
import src.pushover_api as pushover_api
import src.plex_autoscan as plex_autoscan
import src.git_api as git_api


def main():
    banner.script_start()
    pushover_api.send_notification('Spotify downloader', 'Script started')

    spotify_api.download_liked()
    transform.process_liked()
    download.missing_tracks()
    plex_autoscan.scan(download.downloaded_tracks)

    git_api.commit_files()

    if len(download.downloaded_tracks) >= 1:
        pushover_api.send_notification('Spotify downloader',
                                       f'Successfully downloaded {len(download.downloaded_tracks)} new tracks')
    pushover_api.send_notification('Spotify downloader', f'Script finished')
    print('\r--Done!')


if __name__ == '__main__':
    main()

