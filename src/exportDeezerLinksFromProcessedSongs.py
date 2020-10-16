import json
import csv
# load processed songs from file
processed_songs_path = '../data/processed_songs.json'
deezer_url_path = '../data/deezer_urls.txt'
songs_to_export = []
with open(processed_songs_path, 'r+') as psp:
    processed_songs: object = json.load(psp)
    songs_added = 0
    for song in processed_songs:
        if song['matched'] == True and song['downloaded'] == False:
            song['downloaded'] == True
            songs_to_export.append(song['deezer_url'])
            songs_added = songs_added +1
            print(f'Added {str(songs_added)} of {len(processed_songs)} total')
    psp.seek(0)
    json.dump(processed_songs, psp)

print('Saving to file..')
with open(deezer_url_path, mode='w', encoding='utf-8') as myfile:
    myfile.write('\n'.join(songs_to_export))

print('-----Done')
# deemix -b FLAC -l /mnt/kyrie/