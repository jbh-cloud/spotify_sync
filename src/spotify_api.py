import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
from tabulate import tabulate
import os

# Local imports
from src import config
from src.log import rootLogger

logger = rootLogger.getChild('SPOTIFY_API')
config = config.load()

sp = None

def cache_spotify_auth():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        open_browser=False,
        username=config['spotify']['username'],
        scope=config['spotify']['scope'],
        client_id=config['spotify']['client_id'],
        client_secret=config['spotify']['client_secret'],
        redirect_uri=f'http://127.0.0.1:{config["spotify"]["redirect_uri_port"]}',
        cache_path=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            f'.cache-{config["spotify"]["username"]}')
        )
    )

    query = sp.current_user_saved_tracks()
    return


def initialize_spotipy():
    global sp
    if not sp:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            open_browser=False,
            username=config['spotify']['username'],
            scope=config['spotify']['scope'],
            client_id=config['spotify']['client_id'],
            client_secret=config['spotify']['client_secret'],
            redirect_uri=f'http://127.0.0.1:{config["spotify"]["redirect_uri_port"]}',
            cache_path=os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                f'.cache-{config["spotify"]["username"]}')
            )
        )


def get_all_playlists(playlists_to_exclude):
    initialize_spotipy()

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
                logger.debug(f'{playlist["name"]} was in exlude list, skipping')
    return ret


def get_all_songs_from_playlists(playlists):
    initialize_spotipy()
    songs = []

    for k in playlists:
        playlist = playlists[k]
        playlist_songs = []

        logger.debug(f'Fetching songs for playlist: {playlist["name"]}')
        results = sp.playlist_tracks(playlist["id"])
        playlist_songs.extend(results['items'])
        idx = 1
        while results['next']:
            logger.debug(f'Sending Spotify API call {idx}')
            results = sp.next(results)
            playlist_songs.extend(results['items'])
            idx += 1
        logger.debug(f'{len(playlist_songs)} song(s)')
        songs.extend(playlist_songs)

    return songs


def generate_playlist_songs_mapping():
    initialize_spotipy()

    playlists = get_all_playlists(config['script']['spotify_playlists']['excluded'])

    ret = {}

    for k in playlists:
        playlist = playlists[k]

        ret[k] = {
            "playlist_name": playlist["name"],
            "playlist_id": k,
            "tracks": []
        }

        results = sp.playlist_tracks(playlist["id"])
        for t in results['items']:
            try:
                ret[k]['tracks'].append(t['track']['external_ids']['isrc'])
            except KeyError:
                logger.debug(f'Failed getting ISRC for {t["track"]["name"]}')
        idx = 1
        while results['next']:
            logger.debug(f'Sending Spotify API call {idx}')
            results = sp.next(results)
            for t in results['items']:
                try:
                    ret[k]['tracks'].append(t['track']['external_ids']['isrc'])
                except KeyError:
                    logger.debug(f'Failed getting ISRC for {t["track"]["name"]}')
            idx += 1

    return ret


def load_liked():
    path = config['script']['paths']['liked_songs']
    if os.path.isfile(path):
        with open(path, mode='r', encoding='utf-8') as f:
            ret = json.load(f)
    else:
        ret = {}

    logger.info(f'Loaded {str(len(ret))} liked songs from disk')
    return ret


def save_liked(liked):
    logger.debug(f'Serializing {str(len(liked))} liked songs back to disk')
    path = config['script']['paths']['liked_songs']
    with open(config['script']['paths']['liked_songs'], mode='w', encoding='utf-8') as f:
        json.dump(liked, f, indent=4, sort_keys=True)


def fetch_spotify_liked(manual_user=False):
    logger.info('Fetching liked songs')
    if not manual_user:
        initialize_spotipy()
    results = sp.current_user_saved_tracks()
    songs = results['items']
    idx = 1
    while results['next']:
        logger.debug(f'Sending Spotify API call {idx}')
        results = sp.next(results)
        songs.extend(results['items'])
        idx += 1
    return songs


def merge_spotify_playlist_songs(liked_songs):
    logger.info("Fetching playlist songs")
    playlist_songs = get_all_songs_from_playlists(get_all_playlists(config['script']['spotify_playlists']['excluded']))
    logger.debug(f'{len(playlist_songs)} playlist songs')
    added_playlist_songs = 0
    for s in playlist_songs:
        if 'isrc' in s['track']['external_ids']:
            if s['track']['external_ids']['isrc'] not in liked_songs:
                liked_songs[s['track']['external_ids']['isrc']] = s
                added_playlist_songs += 1
            else:
                logger.debug(f'Playlist song with id {s["track"]["external_ids"]["isrc"]} already in liked songs')
        else:
            logger.debug(f'No ISRC: {s["track"]["name"]} - {s["track"]["artists"][0]["name"]}, skipping')
    logger.info(f'Adding {added_playlist_songs}/{len(playlist_songs)} from playlists')
    return liked_songs


def merge_offline_online_liked(offline_dict, online_dict):
    ret = offline_dict.copy()
    new_liked_songs = 0
    for s in online_dict:
        isrc = s['track']['external_ids']['isrc']
        if isrc not in ret:
            ret[isrc] = s
            new_liked_songs += 1

    logger.info(f'Added {str(new_liked_songs)} new liked songs from Spotify')
    return ret


def serialize_playlist_mapping():
    path = config['script']['paths']['playlist_mapping']
    mapping = generate_playlist_songs_mapping()
    logger.debug ('Serializing playlist mapping to disk')
    with open(path, mode='w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=4, sort_keys=True)


def download_liked():
    offline_liked = load_liked()   
    online_liked = fetch_spotify_liked()

    liked = merge_offline_online_liked(offline_liked, online_liked)

    if config['script']['spotify_playlists']['enabled']:
        liked = merge_spotify_playlist_songs(liked)
        serialize_playlist_mapping()

    save_liked(liked)


def download_liked_manual(client_id, client_secret, username, liked_songs_path):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        username=username,
        scope=config['spotify']['scope'],
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=f'http://127.0.0.1:{config["spotify"]["redirect_uri_port"]}',
        cache_path=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            f'.cache-{config["spotify"]["username"]}')
        )
    )
    liked = fetch_spotify_liked(manual_user=True)
    ret = {}
    for s in liked:
        ret[s['track']['external_ids']['isrc']] = s
    with open(liked_songs_path, mode='w', encoding='utf-8') as f:
        json.dump(ret, f, indent=4, sort_keys=True)


def get_playlist_stats():
    initialize_spotipy()
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
