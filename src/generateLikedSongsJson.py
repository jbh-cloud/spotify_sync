from src.functions import *

# Load spotify liked songs object
results = sp.current_user_saved_tracks()
songs = results['items']
while results['next']:
    results = sp.next(results)
    songs.extend(results['items'])

# Write object to disk
liked_songs_path = '../data/spotify_liked_songs.json'

try:
    with open (liked_songs_path, 'r+') as lsp:
        liked_songs = json.load(lsp)
        liked_songs.extend(songs)
        lsp.seek(0)
        json.dump(liked_songs, lsp)
except json.decoder.JSONDecodeError as ex:
    print('Failed to load offline liked songs file')
    raise ex



