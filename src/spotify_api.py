import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
from tabulate import tabulate

# Local imports
from src import config
from src.log import rootLogger

logger = rootLogger.getChild('SPOTIFY_API')
config = config.load()


def cache_spotify_auth():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(username=config['spotify']['username'],
                                                   scope=config['spotify']['scope'],
                                                   client_id=config['spotify']['client_id'],
                                                   client_secret=config['spotify']['client_secret'],
                                                   redirect_uri=f'http://127.0.0.1:{config["spotify"]["redirect_uri_port"]}'))

    query = sp.current_user_saved_tracks()
    return


def get_all_playlists(playlists_to_exclude):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        username=config['spotify']['username'],
        scope=config['spotify']['scope'],
        client_id=config['spotify']['client_id'],
        client_secret=config['spotify']['client_secret'],
        redirect_uri=f'http://127.0.0.1:{config["spotify"]["redirect_uri_port"]}')
    )

    results = sp.user_playlists(config['spotify']['username'])
    playlists = results['items']
    idx = 1
    while results['next']:
        logger.debug(f'Sending Spotify API call {idx}')
        results = sp.next(results)
        playlists.extend(results['items'])
        idx += 1

    ret = {}
    for playlist in playlists:
        if playlist['owner']['id'] == config['spotify']['username']:
            if playlist['name'] not in playlists_to_exclude:
                ret[playlist["id"]] = playlist
            else:
                logger.info(f'{playlist["name"]} was in exlude list, skipping')
    return ret


def get_all_songs_from_playlists(playlists):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        username=config['spotify']['username'],
        scope=config['spotify']['scope'],
        client_id=config['spotify']['client_id'],
        client_secret=config['spotify']['client_secret'],
        redirect_uri=f'http://127.0.0.1:{config["spotify"]["redirect_uri_port"]}')
    )
    songs = []

    for k in playlists:
        playlist = playlists[k]
        playlist_songs = []

        logger.info(f'Fetching songs for playlist: {playlist["name"]}')
        results = sp.playlist_tracks(playlist["id"])
        playlist_songs.extend(results['items'])
        idx = 1
        while results['next']:
            logger.debug(f'Sending Spotify API call {idx}')
            results = sp.next(results)
            playlist_songs.extend(results['items'])
            idx += 1
        logger.info(f'{len(playlist_songs)} song(s)')
        songs.extend(playlist_songs)

    return songs


def download_liked():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        username=config['spotify']['username'],
        scope=config['spotify']['scope'],
        client_id=config['spotify']['client_id'],
        client_secret=config['spotify']['client_secret'],
        redirect_uri=f'http://127.0.0.1:{config["spotify"]["redirect_uri_port"]}')
    )

    logger.info('Fetching liked songs')
    results = sp.current_user_saved_tracks()
    songs = results['items']
    idx = 1
    while results['next']:
        logger.debug(f'Sending Spotify API call {idx}')
        results = sp.next(results)
        songs.extend(results['items'])
        idx += 1

    ret = {}
    for s in songs:
        ret[s['track']['external_ids']['isrc']] = s

    if config['script']['spotify_playlists']['enabled']:
        logger.info("Fetching playlist songs")
        playlist_songs = get_all_songs_from_playlists(get_all_playlists(config['script']['spotify_playlists']['excluded']))
        logger.info(f'{len(playlist_songs)} playlist songs')
        added_playlist_songs = 0
        for s in playlist_songs:
            if 'isrc' in s['track']['external_ids']:
                if s['track']['external_ids']['isrc'] not in ret:
                    ret[s['track']['external_ids']['isrc']] = s
                    added_playlist_songs += 1
                else:
                    logger.debug(f'Playlist song with id {s["track"]["external_ids"]["isrc"]} already in liked songs')
            else:
                logger.debug(f'No ISRC: {s["track"]["name"]} - {s["track"]["artists"][0]["name"]}, skipping')
        logger.info(f'Adding {added_playlist_songs}/{len(playlist_songs)} from playlists')

    logger.debug('Saving liked songs')
    with open(config['script']['paths']['liked_songs'], mode='w', encoding='utf-8') as f:
        json.dump(ret, f, indent=4, sort_keys=True)


def download_liked_manual(client_id, client_secret, username, liked_songs_path):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        username=username,
        scope=config['spotify']['scope'],
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=f'http://127.0.0.1:{config["spotify"]["redirect_uri_port"]}')
    )

    print('Fetching liked songs..')
    results = sp.current_user_saved_tracks()
    songs = results['items']

    while results['next']:
        results = sp.next(results)
        songs.extend(results['items'])

    ret = {}

    for s in songs:
        ret[s['track']['external_ids']['isrc']] = s

    with open(liked_songs_path, mode='w', encoding='utf-8') as f:
        json.dump(ret, f, indent=4, sort_keys=True)


def get_playlist_stats():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        username=config['spotify']['username'],
        scope=config['spotify']['scope'],
        client_id=config['spotify']['client_id'],
        client_secret=config['spotify']['client_secret'],
        redirect_uri=f'http://127.0.0.1:{config["spotify"]["redirect_uri_port"]}')
    )
    ret = []

    playlists = get_all_playlists(config['script']['spotify_playlists']['excluded'])
    for k in playlists:
        playlist = playlists[k]
        ret.append({
            "name": playlist["name"],
            "id": playlist["id"],
            "collaborative": playlist["collaborative"],
            "public": playlist["public"],
            "tracks": playlist["tracks"]["total"],
            "url": playlist["external_urls"]["spotify"]
        })
    return ret


def display_playlist_stats():
    stats = get_playlist_stats()
    header = stats[0].keys()
    rows = [x.values() for x in stats]
    print()
    print(tabulate(rows, header))
