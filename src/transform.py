from dataclasses import dataclass
from typing import Dict
from tabulate import tabulate

# local imports
from src.config import load as load_config
from src.io_ import verify_files, load_liked_songs, load_processed_songs, persist_processed_songs
from src.log import rootLogger
from src.spotify_ import SpotifySong
from src.deezer_ import SongMatcher

logger = rootLogger.getChild('TRANSFORM')
config = load_config()


@dataclass
class ProcessedSong:
    """Class for keeping track of an offline song."""
    spotify_title: str = None
    spotify_artist: str = None
    spotify_isrc: str = None
    spotify_url: str = None
    spotify_id: str = None
    deezer_title: str = None
    deezer_artist: str = None
    deezer_isrc: str = None
    deezer_url: str = None
    deezer_id: str = None
    matched: str = None
    match_type: str = None
    match_message: str = None
    match_pending_download: str = None
    downloaded: str = None
    download_isrc: str = None
    download_url: str = None
    download_path: str = None
    download_md5: str = None
    download_bitrate: str = None
    download_failed: str = None
    download_failed_reason: str = None


def as_spotify_song(songs: Dict[str, SpotifySong]):
    ret = {}
    for k in songs:
        s = SpotifySong()
        s.from_dict(songs[k])
        ret[k] = s

    return ret


def as_processed_song(songs: Dict[str, ProcessedSong]):
    ret = {}
    for k in songs:
        s = ProcessedSong(**songs[k])
        ret[k] = s

    return ret


def get_unprocessed_songs(spotify_songs: Dict[str, SpotifySong], processed_songs):
    ret = {}
    for k in spotify_songs:
        if k not in processed_songs:
            ret[k] = spotify_songs[k]
    return ret


def process_match(matcher: SongMatcher, processed_songs, count_matched: int):
    if matcher.match:
        if 'link' not in matcher.match_payload:
            logger.warning(f'[SpotifyId:{matcher.song.id_}] - Matched but response does not contain a Deezer link, unmatching..')
            matcher.match = False
            matcher.match_message = "Matched but response does not contain a Deezer link"

    s = ProcessedSong(
        spotify_title=matcher.song.title,
        spotify_artist=matcher.song.artist,
        spotify_isrc=matcher.song.isrc,
        spotify_url=matcher.song.url,
        spotify_id=matcher.song.id_,
        deezer_title=matcher.match_payload['title'] if matcher.match else None,
        deezer_artist=matcher.match_payload['artist']['name'] if matcher.match else None,
        # deezer fuzzy search payload doesnt return isrc of matched item
        deezer_isrc=matcher.match_payload.get('isrc') if matcher.match else None,
        deezer_url=matcher.match_payload['link'] if matcher.match else None,
        deezer_id=matcher.match_payload['id'] if matcher.match else None,
        matched=matcher.match,
        match_type=matcher.match_type,
        match_message=matcher.match_message,
        match_pending_download=matcher.match
    )

    processed_songs[s.spotify_id] = s

    return s.matched



def match_unprocessed(unprocessed_songs: Dict[str, SpotifySong], processed_songs):
    logger.info(f'Attempting to match {len(unprocessed_songs)} Spotify songs to Deezer')
    matched = 0
    for k in unprocessed_songs:
        song = unprocessed_songs[k]
        logger.debug(f'Processing: {song.title} - {song.artist}')
        m = SongMatcher(song=song)
        m.search()
        if process_match(m, processed_songs, matched):
            matched += 1

    logger.info(f'Matched {matched}/{len(unprocessed_songs)} new liked song(s)')


def process_liked():
    verify_files()

    liked_songs = as_spotify_song(load_liked_songs())
    processed_songs = as_processed_song(load_processed_songs())

    unprocessed_songs = get_unprocessed_songs(liked_songs, processed_songs)
    logger.info(f'{len(unprocessed_songs)} new songs to process')

    match_unprocessed(unprocessed_songs, processed_songs)
    persist_processed_songs(processed_songs)


def get_songs_to_download():
    logger.debug(f'Opening {config["DATA_FILES_PROCESSED_SONGS"]}')
    processed_songs = as_processed_song(load_processed_songs())

    ret = []
    for k in processed_songs.keys():
        song = processed_songs[k]
        if song.match_pending_download and not song.download_failed:
            logger.debug(f'{k} is matched and awaiting download')
            ret.append(processed_songs[k])

    return ret


def save_processed(processed):
    logger.debug(f'Serializing {str(len(processed))} processed songs back to disk')
    persist_processed_songs(processed)


def persist_download_status(download_statuses):
    processed_songs = as_processed_song(load_processed_songs())

    for k in download_statuses:
        status = download_statuses[k]

        if status.success:
            processed_songs[k].match_pending_download = False
            processed_songs[k].downloaded = True
            processed_songs[k].download_isrc = status.downloaded_isrc
            processed_songs[k].download_url = status.downloaded_url
            processed_songs[k].download_path = status.download_path
            processed_songs[k].download_md5 = status.md5
            processed_songs[k].download_bitrate = status.downloaded_bitrate
            processed_songs[k].download_failed = False
            processed_songs[k].download_failed_reason = None
        else:
            processed_songs[k].match_pending_download = True
            processed_songs[k].downloaded = False
            processed_songs[k].download_isrc = status.downloaded_isrc
            processed_songs[k].download_url = status.downloaded_url
            processed_songs[k].download_path = status.download_path
            processed_songs[k].download_md5 = status.md5
            processed_songs[k].download_failed = True
            processed_songs[k].download_failed_reason = "\n".join([v['message'] for v in status.errors])

    save_processed(processed_songs)


def get_failed_download_stats():
    ret = []

    processed_songs = as_processed_song(load_processed_songs())
    for k in processed_songs:
        song = processed_songs[k]
        if song.download_failed:
            ret.append({
                'spotifyId': song.spotify_id,
                'deezerId': song.deezer_id,
                'title': song.deezer_title,
                'artist': song.deezer_artist,
                'error': song.download_failed_reason
            })

    return ret


def get_failed_download_status_summary():
    ret = {}
    processed_songs = as_processed_song(load_processed_songs())
    for k in processed_songs:
        song = processed_songs[k]
        if song.download_failed:
            if song.download_failed_reason not in ret:
                ret[song.download_failed_reason] = 1
            else:
                ret[song.download_failed_reason] += 1

    return [{'Failed downloads': v, 'Reason': k} for k, v in ret.items()]


def display_failed_download_stats():
    stats = get_failed_download_status_summary()
    # stats = get_failed_download_stats()
    if len(stats) == 0:
        logger.info(f'No failed downloads')
        return

    header = stats[0].keys()
    rows = [x.values() for x in stats]
    print()
    print(tabulate(rows, header))










