import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json, sys, itertools, threading, time
import src.config as config
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


def download_liked():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        username=config['spotify']['username'],
        scope=config['spotify']['scope'],
        client_id=config['spotify']['client_id'],
        client_secret=config['spotify']['client_secret'],
        redirect_uri=f'http://127.0.0.1:{config["spotify"]["redirect_uri_port"]}')
    )

    logger.info('Fetching liked songs')
    #print('Fetching liked songs..')

    # Load spotify liked songs object
    idx = 1
    results = sp.current_user_saved_tracks()
    songs = results['items']
    while results['next']:
        logger.debug(f'Sending Spotify API call {idx}')
        results = sp.next(results)
        songs.extend(results['items'])
        idx += 1

    ret = {}
    for s in songs:
        ret[s['track']['external_ids']['isrc']] = s

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

    # Load spotify liked songs object
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
