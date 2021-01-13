import deezer as Deezer
import src.config as config
import json

config = config.load()

# load Deezer and login (for downloads), API is unauthenicated
client = Deezer.Deezer()
#client.login_via_arl(config['deezer']['arl'])


def match_isrc(song):
    try:
        track = Deezer.API.get_track(client.api, f'isrc:{song["track"]["external_ids"]["isrc"]}')
        return True, {
            'spotify_title': song['track']['name'],
            'spotify_artist': song['track']['artists'][0]['name'],
            'spotify_isrc': song["track"]["external_ids"]["isrc"],
            'spotify_url': song['track']['external_urls']['spotify'],
            'spotify_id': song['track']['id'],
            'deezer_title': track['title'],
            'deezer_artist': track['artist']['name'],
            'deezer_url': track['link'],
            'deezer_id': track['id'],
            'matched': True,
            'match_type': 'isrc',
            'match_pending_download': True,
            'downloaded': False
        }
    except:
        return False, {}

def match_adv(song):
    deezer_search = Deezer.API.advanced_search(
        client.api, # self
        song['track']['artists'][0]['name'], # artist
        '', # album
        song['track']['name'] # track name
    )

    if len(deezer_search['data']) >= 1:
        most_likely = deezer_search['data'][0]
        return True, {
            'spotify_title': song['track']['name'],
            'spotify_artist': song['track']['artists'][0]['name'],
            'spotify_isrc': song["track"]["external_ids"]["isrc"],
            'spotify_url': song['track']['external_urls']['spotify'],
            'spotify_id': song['track']['id'],
            'deezer_title': most_likely['title'],
            'deezer_artist': most_likely['artist']['name'],
            'deezer_url': most_likely['link'],
            'deezer_id': most_likely['id'],
            'matched': True,
            'match_type': 'fuzzy',
            'match_pending_download': True,
            'downloaded': False
        }
    else:
        return False, {
            'spotify_title': song['track']['name'],
            'spotify_artist': song['track']['artists'][0]['name'],
            'spotify_isrc': song["track"]["external_ids"]["isrc"],
            'spotify_url': song['track']['external_urls']['spotify'],
            'spotify_id': song['track']['id'],
            'deezer_title': '',
            'deezer_artist': '',
            'deezer_url': '',
            'deezer_id': '',
            'matched': False,
            'match_type': None,
            'match_pending_download': False,
            'downloaded': False
        }