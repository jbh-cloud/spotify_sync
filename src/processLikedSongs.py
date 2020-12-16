import json
import deemix
import deezer
#import social_core
import time

#SOCIAL_AUTH_AUTHENTICATION_BACKENDS = ('social_core.backends.deezer.DeezerOAuth2')

def large_array(incrementor: int, end: int):
     list = []
     for i in range(0, end, incrementor):
          list.append(i)
     return list


# load liked songs from file
liked_songs_path = '../data/spotify_liked_songs.json'
with open(liked_songs_path, 'r') as f:
     liked_songs: object = json.load(f)

# load processed songs from file
liked_songs_path = '../data/processed_songs.json'
with open(liked_songs_path, 'r') as f:
     processed_songs: object = json.load(f)

# load Deezer API client
client = deezer.Client()

# need to find out how to search deezer for track via isrc

all_song_information = []

for i, song in enumerate(liked_songs):
     if (i+1) % 50 == 0:
          print('Sleeping for 5 secs')
          time.sleep(5)
     print(str(i + 1) + '/' + str(len(liked_songs)))
     title = song['track']['name']
     artist = song['track']['artists'][0]['name']
     isrc = song['track']['external_ids']['isrc']

     # try search via ISRC first
     track = client.get_track(f'isrc:{isrc}')
     if track:
          print(f'Matched track with ISRC: {isrc}')
          all_song_information.append({
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
               'downloaded': False
          })
     else:
          print(f'Failed to match track with ISRC: {isrc}, attempting fuzzy search')
          deezer_search = client.advanced_search({"artist": artist, "track": title}, relation='track')
          if len(deezer_search) >= 1:
               most_likely = deezer_search[0]
               all_song_information.append({
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
                    'downloaded': False
               })
          else:
               #print('Unable to find ' + artist + ' - ' + title + ' on Deezer')
               all_song_information.append({
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
                    'downloaded': False
               })

processed_songs_path = '../data/processed_songs.json'

with open (processed_songs_path, 'w') as psp:
   json.dump(all_song_information, psp)


print('--- All done')