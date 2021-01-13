import src.generateLikedSongsJson as downloadSpotifyLikedSongs
import src.processLikedSongs as processLikedSongs
import src.exportDeezerLinksFromProcessedSongs as exportDeezerLinks
import src.spotify_api as spotify_api
import src.transform as transform
import src.banner as banner
import src.download as download

def main():
    banner.script_start()

    # Download latest Spotify likes
    spotify_api.download_liked()

    # Check for new (unprocessed) liked songs and attempt to match to Deezer, save to processed_songs
    transform.process_liked()

    # Download pending songs
    download.missing_tracks()

    # Generate Deezer file for any new songs
    #exportDeezerLinks.run(processed_songs_path, deezer_url_path)


if __name__ == '__main__':
    main()

