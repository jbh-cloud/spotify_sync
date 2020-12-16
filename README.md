# spotify_download

### Overview
This project was written to allow me to save my Spotify tracks in flac and a safe location to safe guard from Spotify licensing deals expiring. This allows me to have an 'archive' of my historical likes.

It doesn't actually do any downloading (it could) but generates the required files that will later be fed into deemix.

This is broken down into:

```generateLikedSongsJson.py``` 
- Query Spotify API to retrieve all liked songs
- Save these (in Spotify format) as spotify_liked_songs.json

```processLikedSongs.py```
- Load spotify_liked_songs.json
- Query Deezer API for each track (takes some time due to Deezer API limit) and return Deezer information if matched
- Save both sets of data back into processed_songs.json

```exportDeezerLinksFromProcessedSongs.py```

- Load processed_songs.json
- Read all deezer url's present and save into deezer_urls.txt


