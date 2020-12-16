import json
import csv
# load processed songs from file
processed_songs_path = '../data/processed_songs.json'
deezer_url_path = '../data/deezer_urls.txt'

print(f'Reading {processed_songs_path}')
with open(processed_songs_path, mode='r', encoding='utf-8') as f:
    processed_songs = json.load(f)

ret = []
songs_added = 0
print(f'Finding non downloaded tracks')
for k in processed_songs.keys():
    song = processed_songs[k]
    if song['matched'] == True and song['downloaded'] == False:
        song['downloaded'] == True
        ret.append(song['deezer_url'])
        songs_added = songs_added +1
        print(f'Adding {songs_added} of {len(processed_songs)} total')


print(f'Saving changes to {processed_songs_path}')
with open(processed_songs_path, mode='w', encoding='utf-8') as f:
    json.dump(processed_songs, f, indent=4, sort_keys=True)


print(f'Outputing download links to {deezer_url_path}')
with open(deezer_url_path, mode='w', encoding='utf-8') as myfile:
    myfile.write('\n'.join(ret))

print('-----Done')
# deemix -b FLAC -l /mnt/kyrie/