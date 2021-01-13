import src.spotify_api as spotify_api
import src.transform as transform
import src.banner as banner
import src.download as download
import src.pushover_api as pushover_api

def main():
    banner.script_start()
    pushover_api.send_notification('Spotify downloader', 'Script started')

    spotify_api.download_liked()
    transform.process_liked()
    download.missing_tracks()

    pushover_api.send_notification('Spotify downloader', 'Script finished')
    print('\r--Done!')

if __name__ == '__main__':
    main()

