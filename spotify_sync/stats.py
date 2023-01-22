from typing import List, Union
from tabulate import tabulate

# local imports
from spotify_sync.spotify_ import SpotifyService
from spotify_sync.io_ import PersistentDataService

pd_svc: Union[None, PersistentDataService] = None
spotify_svc: Union[None, SpotifyService] = None


def display_user_playlists(sp_svc: SpotifyService):
    global spotify_svc
    spotify_svc = sp_svc

    stats = get_playlist_stats()
    if len(stats) == 0:
        print("No playlists found")
        return

    header = stats[0].keys()
    rows = [x.values() for x in stats]
    print()
    print(tabulate(rows, header))
    print()


def display_failed_download_summary(pd: PersistentDataService) -> None:
    global pd_svc
    pd_svc = pd

    stats = get_failed_download_status_summary()
    if len(stats) == 0:
        print("No failed downloads")
        return

    header = stats[0].keys()
    rows = [x.values() for x in stats]
    print()
    print(tabulate(rows, header))
    print()


def display_failed_match_summary(pd: PersistentDataService):
    global pd_svc
    pd_svc = pd
    stats = get_failed_match_songs()
    if len(stats) == 0:
        print("No failed matches")
        return

    header = stats[0].keys()
    rows = [x.values() for x in stats]
    print()
    print(tabulate(rows, header))
    print()


def get_failed_match_songs() -> List[dict]:
    assert pd_svc is not None

    ret = []
    processed_songs = pd_svc.load_processed_songs()
    for k, song in processed_songs.items():
        if song.matched:
            continue

        ret.append(
            {
                "title": song.spotify_title,
                "artist": song.spotify_artist,
                "isrc": song.spotify_isrc,
            }
        )

    return ret


def get_playlist_stats() -> List[dict]:
    assert spotify_svc is not None

    ret = []

    spotify_svc.preflight()
    playlists = spotify_svc.get_all_playlists()
    for k in playlists:
        playlist = playlists[k]
        ret.append(
            {
                "name": playlist["name"],
                "id": playlist["id"],
                "owner": spotify_svc.paginator.is_playlist_owner(playlist),
                "collaborative": playlist["collaborative"],
                "public": playlist["public"],
                "tracks": playlist["tracks"]["total"],
                "url": playlist["external_urls"]["spotify"],
            }
        )

    return ret


def get_failed_download_status_summary() -> List[dict]:
    assert pd_svc is not None

    ret = {}
    processed_songs = pd_svc.load_processed_songs()
    for k, song in processed_songs.items():
        if song.download_failed:
            if song.download_failed_reason not in ret:
                ret[song.download_failed_reason] = 1
                break

            ret[song.download_failed_reason] += 1

    return [{"Failed downloads": v, "Reason": k} for k, v in ret.items()]
