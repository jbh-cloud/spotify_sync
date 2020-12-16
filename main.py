import src.generateLikedSongsJson as downloadSpotifyLikedSongs
import src.processLikedSongs as processLikedSongs
import src.exportDeezerLinksFromProcessedSongs as exportDeezerLinks

liked_songs_path = 'data/spotify_liked_songs.json'
processed_songs_path = 'data/processed_songs.json'
deezer_url_path = 'data/deezer_urls.txt'

print('Spotify liked song downloader v1')

# Download latest Spotify likes
downloadSpotifyLikedSongs.run(liked_songs_path)

# Check for new (unprocessed) liked songs and attempt to match to Deezer
processLikedSongs.run(liked_songs_path, processed_songs_path)

# Generate Deezer file for any new songs
exportDeezerLinks.run(processed_songs_path, deezer_url_path)