from src.functions import *

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(username='jamesbairdhutchinson',
                                                   scope='user-library-read',
                                                   client_id='33bbbfe2ba9a486ebd39ff4db06c689d',
                                                   client_secret='04c970d3e90f499aac43300552a8326a',
                                                   redirect_uri='http://127.0.0.1:9090'))

# Load spotify liked songs object
results = sp.current_user_saved_tracks()
songs = results['items']
idx = 1
while results['next']:
    idx = idx +1
    print(f'API hit: {idx}')
    results = sp.next(results)
    songs.extend(results['items'])

# Trun into key dict

ret = {}
for s in songs:
    ret[s['spotify_isrc']] = s

# Write object to disk
liked_songs_path = '../data/spotify_liked_songs.json'


with open(liked_songs_path, mode='w', encoding='utf-8') as f:
    json.dump(ret, f, indent=4, sort_keys=True)




