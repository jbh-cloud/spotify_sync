import json
#import deemix
import deezer
#import social_core
import time

#SOCIAL_AUTH_AUTHENTICATION_BACKENDS = ('social_core.backends.deezer.DeezerOAuth2')

# load liked songs from file
liked_songs_path = '../data/spotify_liked_songs.json'
print(f'Loading {liked_songs_path}')
with open(liked_songs_path, 'r') as f:
     liked_songs = json.load(f)

# load processed songs from file
processed_songs_path = '../data/processed_songs.json'
print(f'Loading {processed_songs_path}')
with open(processed_songs_path, 'r') as f:
     processed_songs = json.load(f)

# load Deezer API client
client = deezer.Client()

liked_songs_len = len(liked_songs.keys())
i = 1
print(f'Processing {liked_songs_len} Spotify liked songs')
for k in liked_songs.keys():
     if (k in processed_songs.keys()) and processed_songs[k]['matched'] == True:
          print(f'{k} already in processed songs and already successfully matched')
          continue

     if i % 40 == 0:
          print('Sleeping for 5 secs')
          time.sleep(5)

     print(f'{i}/{liked_songs_len}')
     song = liked_songs[k]

     title = song['track']['name']
     artist = song['track']['artists'][0]['name']
     isrc = song['track']['external_ids']['isrc']


     # try search via ISRC first
     try:
          track = client.get_track(f'isrc:{isrc}')
          print(f'Matched track with ISRC: {isrc}')
          processed_songs[isrc] = {
               'spotify_title': title,
               'spotify_artist': artist,
               'spotify_isrc': isrc,
               'spotify_url': song['track']['external_urls']['spotify'],
               'spotify_id': song['track']['id'],
               'deezer_title': track.title,
               'deezer_artist': track.artist.name,
               'deezer_url': track.link,
               'deezer_id': track.id,
               'matched': True,
               'match_type': 'isrc',
               'downloaded': False
          }
     except:
          print(f'Failed to match track with ISRC {isrc}, attempting fuzzy search: "artist": {artist}, "track": {title}')
          deezer_search = client.advanced_search({"artist": artist, "track": title}, relation='track')
          if len(deezer_search) >= 1:
               most_likely = deezer_search[0]
               processed_songs[isrc] = {
                    'spotify_title': title,
                    'spotify_artist': artist,
                    'spotify_isrc': isrc,
                    'spotify_url': song['track']['external_urls']['spotify'],
                    'spotify_id': song['track']['id'],
                    'deezer_title': most_likely.title,
                    'deezer_artist': most_likely.artist.name,
                    'deezer_url': most_likely.link,
                    'deezer_id': most_likely.id,
                    'matched': True,
                    'match_type': 'fuzzy',
                    'downloaded': False
               }
          else:
               print('Unable to find ' + artist + ' - ' + title + ' on Deezer')
               processed_songs[isrc] = {
                    'spotify_title': title,
                    'spotify_artist': artist,
                    'spotify_isrc': isrc,
                    'spotify_url': song['track']['external_urls']['spotify'],
                    'spotify_id': song['track']['id'],
                    'deezer_title': '',
                    'deezer_artist': '',
                    'deezer_url': '',
                    'deezer_id': '',
                    'matched': False,
                    'match_type': None,
                    'downloaded': False
               }
     i = i+1


with open (processed_songs_path, mode='w', encoding='utf-8') as f:
   json.dump(processed_songs, f, indent=4, sort_keys=True)


print('--- All done')