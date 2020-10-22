from src.functions import *

# Load Spotify object
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(username='jamesbairdhutchinson',
                                                   scope='user-library-read user-follow-read',
                                                   client_id='33bbbfe2ba9a486ebd39ff4db06c689d',
                                                   client_secret='04c970d3e90f499aac43300552a8326a',
                                                   redirect_uri='http://127.0.0.1:9090'))

# Load spotify liked songs object
results = sp.current_user_followed_artists()
artists = results['artists']['items']
while results['artists']['next']:
    results = sp.next(results['artists'])
    artists.extend(results['artists']['items'])

# Write object to disk
followed_artists_path = '../data/spotify_followed_artists.json'


with open (followed_artists_path, mode='w', encoding='utf-8') as f:
    print('writing json')
    #followed_artists = json.load(f)
    json.dump(artists, f)
print('closed file')




