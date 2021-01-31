import argparse, sys

# local imports
from src import actions


def main():
    parser = argparse.ArgumentParser(description='Spotify downloader V1')
    required = parser.add_mutually_exclusive_group(required=True)
    required.add_argument('-auto', action='store_true', help='Runs the downloader in automatic mode')
    required.add_argument('-authorize-spotify', action='store_true', required=False,
                          help='Populate OAuth cached creds')
    required.add_argument('-sync-liked', action='store_true', required=False,
                          help='Queries Spotify for liked songs and downloads metadata')
    required.add_argument('-match-liked', action='store_true',
                          help='Queries locally saved liked song metadata and attempts to match on Deezer')
    required.add_argument('-download-missing', action='store_true', help='Attempts to download missing songs')
    required.add_argument('-manual-scan', action='store_true', help='Invokes Autoscan API against provided paths')
    required.add_argument('-playlist-stats', action='store_true', help='Displays stats associated with Spotify playlists')
    parser.add_argument('--paths', required='-manual-scan' in sys.argv, type=str, nargs="*",
                        help='List of paths to scan')
    parser.add_argument('--sync-liked-custom-user', action='store_true', required=False,
                        help='Specifies a custom user to query Spotify for')
    parser.add_argument('--spotify-client-id', required='--sync-liked-custom-user' in sys.argv, type=str,
                        help='Custom Spotify user client id')
    parser.add_argument('--spotify-client-secret', required='--sync-liked-custom-user' in sys.argv, type=str,
                        help='Custom Spotify user client secret')
    parser.add_argument('--spotify-username', required='--sync-liked-custom-user' in sys.argv, type=str,
                        help='Custom Spotify username')
    parser.add_argument('--liked-songs-path', required='--sync-liked-custom-user' in sys.argv, type=str,
                        help='Path to non-existent json file')

    args = parser.parse_args()

    if args.auto:
        actions.auto()
    elif args.sync_liked:
        if args.sync_liked_custom_user:
            actions.sync_liked_custom_user(
                args.client_id,
                args.client_secret,
                args.username,
                args.liked_songs_path
            )
        else:
            actions.sync_liked()
    elif args.authorize_spotify:
        actions.authorize_spotify()
    elif args.match_liked:
        actions.match_liked()
    elif args.download_missing:
        actions.download_missing()
    elif args.manual_scan:
        actions.scan(args.paths)
    elif args.playlist_stats:
        actions.playlist_stats()
    else:
        print('No arguments specified, try main.py --help')


if __name__ == '__main__':
    main()
