import src.generateLikedSongsJson as downloadSpotifyLikedSongs
import src.processLikedSongs as processLikedSongs
import src.exportDeezerLinksFromProcessedSongs as exportDeezerLinks

# Download latest Spotify likes
downloadSpotifyLikedSongs.run()

# Check for new (unprocessed) liked songs and attempt to match to Deezer
processLikedSongs.run()

# Generate Deezer file for any new songs
exportDeezerLinks.run()