import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
from tabulate import tabulate
import os
from typing import List, Dict

# Local imports
from src.config import load as load_config
from src.io_ import persist_liked_songs
from src.log import rootLogger
from src.functions import ensure_directory

logger = rootLogger.getChild('SPOTIFY')
config = load_config()

sp = None


class SpotifySong:
    def __init__(self, id_=None, artist=None, album=None, title=None, url=None, isrc=None, explicit=None):
        self.id_: id_
        self.artist: artist
        self.album: album
        self.title: title
        self.url: url
        self.isrc: isrc
        self.explicit: explicit

    def from_api(self, song: dict):
        self.id_ = song['track']['id']
        self.artist = song['track']['artists'][0]['name']
        self.album = song['track']['album']['name']
        self.title = song['track']['name']
        self.url = song['track']['external_urls'].get('spotify')
        self.isrc = song['track']['external_ids'].get('isrc')
        self.explicit = song['track']['explicit']

    def from_dict(self, dictionary: dict):
        self.id_ = dictionary['id_']
        self.artist = dictionary['artist']
        self.album = dictionary['album']
        self.title = dictionary['title']
        self.url = dictionary['url']
        self.isrc = dictionary['isrc']
        self.explicit = dictionary['explicit']

    def is_valid(self):
        if self.id_ is not None and self.isrc is not None:
            return True
        else:
            logger.debug(f'Track {self.title} has no Spotify id or isrc, skipping..')
            return False


def cache_spotify_auth():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        open_browser=False,
        username=config["SPOTIFY_USERNAME"],
        scope=config["SPOTIFY_SCOPE"],
        client_id=config["SPOTIFY_CLIENT_ID"],
        client_secret=config["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=f'http://127.0.0.1:{config["SPOTIFY_REDIRECT_URI_PORT"]}',
        cache_path=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            f'.cache-{config["SPOTIFY_USERNAME"]}')
        )
    )

    query = sp.current_user_saved_tracks()
    return


def initialize_spotipy():
    global sp
    if not sp:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            open_browser=False,
            username=config["SPOTIFY_USERNAME"],
            scope=config["SPOTIFY_SCOPE"],
            client_id=config["SPOTIFY_CLIENT_ID"],
            client_secret=config["SPOTIFY_CLIENT_SECRET"],
            redirect_uri=f'http://127.0.0.1:{config["SPOTIFY_REDIRECT_URI_PORT"]}',
            cache_path=os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                f'.cache-{config["SPOTIFY_USERNAME"]}')
            )
        )


def get_all_playlists(playlists_to_exclude):
    initialize_spotipy()

    results = sp.user_playlists(config["SPOTIFY_USERNAME"])
    playlists = results['items']
    idx = 1
    while results['next']:
        logger.debug(f'Sending Spotify API call {idx}')
        results = sp.next(results)
        playlists.extend(results['items'])
        idx += 1

    ret = {}
    for playlist in playlists:
        if playlist['owner']['id'] == config["SPOTIFY_USERNAME"]:
            if playlist['name'] not in playlists_to_exclude:
                ret[playlist["id"]] = playlist
            else:
                logger.debug(f'{playlist["name"]} was in exlude list, skipping')
    return ret


def get_all_songs_from_playlists(playlists):
    initialize_spotipy()
    api_songs = []

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
        api_songs.extend(playlist_songs)

    ret = []
    for api_s in api_songs:
        s = SpotifySong()
        s.from_api(api_s)
        if s.is_valid():
            ret.append(s)

    return ret


def generate_playlist_songs_mapping():
    initialize_spotipy()

    playlists = get_all_playlists(config["SPOTIFY_PLAYLISTS_EXCLUDED"])

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
                ret[k]['tracks'].append(t['track']['id'])
            except KeyError:
                logger.warning(f'Failed getting SpotifyId for {t["track"]["name"]}')
        idx = 1
        while results['next']:
            logger.debug(f'Sending Spotify API call {idx}')
            results = sp.next(results)
            for t in results['items']:
                try:
                    ret[k]['tracks'].append(t['track']['id'])
                except KeyError:
                    logger.warning(f'Failed getting SpotifyId for {t["track"]["name"]}')
            idx += 1

    return ret


def load_liked():
    path = os.path.join(config["DATA_PERSISTENT_DATA_ROOT"], config["DATA_FILES_LIKED_SONGS"])
    if os.path.isfile(path):
        with open(path, mode='r', encoding='utf-8') as f:
            ret = json.load(f)
    else:
        ret = {}

    logger.info(f'Loaded {str(len(ret))} liked songs from disk')
    return ret


def save_liked(liked):
    logger.debug(f'Serializing {str(len(liked))} liked songs back to disk')
    persist_liked_songs(liked)


def fetch_spotify_liked(manual_user=False):
    logger.info('Fetching liked songs')
    if not manual_user:
        initialize_spotipy()
    results = sp.current_user_saved_tracks()
    api_songs = results['items']
    idx = 1
    while results['next']:
        logger.debug(f'Sending Spotify API call {idx}')
        results = sp.next(results)
        api_songs.extend(results['items'])
        idx += 1

    ret = []
    for api_s in api_songs:
        s = SpotifySong()
        s.from_api(api_s)
        if s.is_valid():
            ret.append(s)

    return ret


def merge_spotify_playlist_songs(liked_songs: Dict[str, SpotifySong]):
    logger.info("Fetching playlist songs")
    playlist_songs = get_all_songs_from_playlists(get_all_playlists(config["SPOTIFY_PLAYLISTS_EXCLUDED"]))
    logger.debug(f'{len(playlist_songs)} playlist songs')
    added_playlist_songs = 0
    for s in playlist_songs:
        if s.id_ not in liked_songs:
            liked_songs[s.id_] = s
            added_playlist_songs += 1
        else:
            logger.debug(f'Playlist song with id {s.id_} already in liked songs')

    logger.info(f'Adding {added_playlist_songs}/{len(playlist_songs)} from playlists')
    return liked_songs


def merge_offline_online_liked(offline_dict: Dict[str, SpotifySong], online_liked: List[SpotifySong]):
    ret = offline_dict.copy()
    new_liked_songs = 0
    for s in online_liked:
        if s.id_ not in ret:
            ret[s.id_] = s
            new_liked_songs += 1

    logger.info(f'Added {str(new_liked_songs)} new liked song(s) from Spotify')
    return ret


def persist_playlist_mapping():
    path = os.path.join(config["DATA_PERSISTENT_DATA_ROOT"], config["DATA_FILES_PLAYLIST_MAPPING"])
    ensure_directory(path)
    mapping = generate_playlist_songs_mapping()
    logger.debug ('Serializing playlist mapping to disk')
    with open(path, mode='w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=4, sort_keys=True)


def download_liked():
    offline_liked = load_liked()   
    online_liked = fetch_spotify_liked()

    liked = merge_offline_online_liked(offline_liked, online_liked)

    if config["SPOTIFY_PLAYLISTS_ENABLED"]:
        liked = merge_spotify_playlist_songs(liked)
        persist_playlist_mapping()

    save_liked(liked)


def download_liked_manual(client_id, client_secret, username, liked_songs_path):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        username=username,
        scope=config["SPOTIFY_SCOPE"],
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=f'http://127.0.0.1:{config["SPOTIFY_REDIRECT_URI_PORT"]}',
        cache_path=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            f'.cache-{config["SPOTIFY_USERNAME"]}')
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

    playlists = get_all_playlists(config["SPOTIFY_PLAYLISTS_EXCLUDED"])
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
