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
liked_songs_path = 'data/spotify_liked_songs.json'
with open(liked_songs_path, 'r+') as lsp:
     liked_songs: object = json.load(lsp)

ten_songs = liked_songs[0:10]

# load Deezer API
client = deezer.Client()

client.advanced_search({"artist": 'Bastien Keb', "track": 'All That Love in Your Heart'}, relation='track')

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
     #deezer_search = client.search(title, relation='title')
     deezer_search = client.advanced_search({"artist": artist, "track": title}, relation='track')
     if len(deezer_search) >= 1:
          most_likely = deezer_search[0]
          #print('Spotify: ' + artist + ' - ' + title)
          #print('Deezer: ' + most_likely.artist.name + ' - ' + most_likely.title)
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

processed_songs_path = 'data/processed_songs.json'
try:
    with open (processed_songs_path, 'r+') as psp:
        processed_songs = json.load(psp)
        processed_songs.extend(all_song_information)
        psp.seek(0)
        json.dump(processed_songs, psp)
except json.decoder.JSONDecodeError as ex:
    print('Failed to load offline liked songs file')
    raise ex

print('--- All done')