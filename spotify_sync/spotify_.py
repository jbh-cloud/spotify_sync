import sys
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyPKCE, CacheFileHandler
from tabulate import tabulate
from typing import List, Dict, Union

# Local imports
from spotify_sync.config import Config
from spotify_sync.io_ import PersistentDataService
from spotify_sync.dataclasses import SpotifySong


class SpotifyService:
    def __init__(
        self,
        app_config: Config,
        pd_svc: PersistentDataService,
        force_reauth=False,
    ):
        from spotify_sync.log import get_logger

        self._logger = get_logger().getChild("SpotifyService")
        self.config = app_config
        self.pd_svc = pd_svc
        self.sp = spotipy.Spotify(auth_manager=self._get_oauth(force_reauth))
        self.paginator = SpotifyPaginator(self)
        self.songs = []

    def sync(self):
        self.preflight()
        cached = self.pd_svc.load_spotify_songs()
        online = self._fetch_liked()
        liked = self._merge_liked(cached, online)

        mapping = {}
        if self.config.data["SPOTIFY_PLAYLISTS_ENABLED"]:
            liked, playlists = self._merge_playlist_songs(liked)
            mapping = self._generate_playlist_songs_mapping(playlists)

        self.pd_svc.persist_playlist_mapping(mapping)
        self.pd_svc.persist_spotify_songs(liked)

    def cache_spotify_auth(self):
        auth = self._get_oauth()

        def _auth_headers():
            try:
                token = auth.get_access_token(as_dict=False)
            except TypeError:
                token = auth.get_access_token()
            return {"Authorization": "Bearer {0}".format(token)}

        _auth_headers()

    def _generate_playlist_songs_mapping(self, playlists: dict):
        ret = {}
        for k, playlist in playlists.items():
            ret[k] = {
                "playlist_name": playlist["name"],
                "playlist_id": k,
                "tracks": [],
            }
            songs = self.paginator.get_songs_from_playlists(playlist=playlist)
            ret[k]["tracks"] = [v.id_ for v in songs]

        return ret

    def get_all_playlists(self, playlists_to_exclude=[]):
        return self.paginator.user_playlists(playlists_to_exclude)

    def _get_all_playlist_songs(self, playlists):
        return self.paginator.get_songs_from_playlists(playlists=playlists)

    def _fetch_liked(self) -> List[SpotifySong]:
        self._logger.info("Fetching liked songs")
        return self.paginator.user_liked()

    def _merge_liked(
        self, cached: Dict[str, SpotifySong], online: List[SpotifySong]
    ):
        ret = cached.copy()
        new_liked_songs = 0
        for s in online:
            if s.id_ not in ret:
                ret[s.id_] = s
                new_liked_songs += 1

        self._logger.info(
            f"Added {str(new_liked_songs)} new liked song(s) from Spotify (cached:{len(cached)})"
        )
        return ret

    def _merge_playlist_songs(self, songs: Dict[str, SpotifySong]):
        self._logger.info("Fetching playlist songs")
        playlists = self.get_all_playlists(
            self.config.data["SPOTIFY_PLAYLISTS_EXCLUDED"]
        )
        playlist_songs = self._get_all_playlist_songs(playlists)
        self._logger.debug(f"{len(playlist_songs)} playlist songs")
        added_playlist_songs = 0
        for s in playlist_songs:
            if s.id_ not in songs:
                songs[s.id_] = s
                added_playlist_songs += 1

        self._logger.info(
            f"Adding {added_playlist_songs}/{len(playlist_songs)} from playlists"
        )
        return songs, playlists

    def _get_oauth(
        self, force_reauth=False
    ) -> Union[SpotifyOAuth, SpotifyPKCE]:
        if force_reauth:
            self.pd_svc.get_spotify_oauth().unlink(missing_ok=True)

        handler = CacheFileHandler(cache_path=self.pd_svc.get_spotify_oauth())

        if self.config.data["SPOTIFY_CUSTOM_APPLICATION_ENABLED"]:
            return SpotifyOAuth(
                open_browser=False,
                scope=self.config.data["SPOTIFY_CUSTOM_APPLICATION_SCOPE"],
                client_id=self.config.data[
                    "SPOTIFY_CUSTOM_APPLICATION_CLIENT_ID"
                ],
                client_secret=self.config.data[
                    "SPOTIFY_CUSTOM_APPLICATION_CLIENT_SECRET"
                ],
                redirect_uri=f'http://127.0.0.1:{self.config.data["SPOTIFY_CUSTOM_APPLICATION_REDIRECT_URI_PORT"]}',
                cache_handler=handler,
            )
        else:
            return SpotifyPKCE(
                open_browser=False,
                scope="user-library-read, playlist-read-private, playlist-read-collaborative",
                client_id="33bbbfe2ba9a486ebd39ff4db06c689d",
                redirect_uri="http://127.0.0.1:9090",
                cache_handler=handler,
            )

    def _oauth_is_cached(self):
        return (
            self.pd_svc.get_spotify_oauth().exists()
            and self.pd_svc.get_spotify_oauth().is_file()
        )

    def preflight(self):
        if not self._oauth_is_cached():
            command_sffx = (
                f"--profile {self.config.profile}"
                if self.config.profile is not None
                else f"--config {self.config.path}"
            )
            self._logger.error(
                f'No Spotify OAuth token found, please cache one using "spotify_sync utils authorize-spotify {command_sffx}"'
            )
            sys.exit(1)


class SpotifyPaginator:
    def __init__(self, spotify_svc: SpotifyService):
        from spotify_sync.log import get_logger

        self._logger = get_logger().getChild("SpotifyPaginator")
        self.spotify_svc = spotify_svc

    def user_liked(self) -> List[SpotifySong]:
        response = self._get_all("liked")
        return self._to_spotify_song(response)

    def user_playlists(self, playlists_to_exclude) -> dict:
        return self._get_all(
            "playlists", playlists_to_exclude=playlists_to_exclude
        )

    def get_songs_from_playlists(
        self, playlist=None, playlists=None
    ) -> List[SpotifySong]:
        if playlist is not None:
            response = self._get_all("playlist-songs", playlist=playlist)
        else:
            response = self._get_all("playlist-songs", playlists=playlists)

        return self._to_spotify_song(response)

    def _exclude_playlists(self, playlists, playlists_to_exclude) -> dict:
        ret = {}
        for playlist in playlists:
            if playlist["name"] not in playlists_to_exclude:
                ret[playlist["id"]] = playlist
            else:
                self._logger.debug(
                    f'{playlist["name"]} was in exclude list, skipping'
                )

        return ret

    def _get_all(self, route: str, **kwargs) -> dict:
        assert route in ["liked", "playlists", "playlist-songs"]

        if route == "liked":
            return self._page_api(
                self.spotify_svc.sp.current_user_saved_tracks(limit=50)
            )

        if route == "playlists":
            playlists = self._page_api(
                self.spotify_svc.sp.current_user_playlists(limit=50)
            )
            if "playlists_to_exclude" in kwargs:
                playlists = self._exclude_playlists(
                    playlists, kwargs["playlists_to_exclude"]
                )

            if self.spotify_svc.config.data["SPOTIFY_PLAYLISTS_OWNER_ONLY"]:
                playlists = self._filter_playlists_by_owner(playlists)

            return playlists

        if route == "playlist-songs":
            if "playlist" not in kwargs and "playlists" not in kwargs:
                raise Exception(
                    "Must provide either playlist or playlists to extract songs from"
                )

            if "playlist" in kwargs:
                return self._page_api(
                    self.spotify_svc.sp.playlist_items(
                        kwargs["playlist"]["id"]
                    )
                )

            ret = []
            for k, playlist in kwargs["playlists"].items():
                self._logger.debug(
                    f'Fetching songs for playlist: {playlist["name"]}'
                )
                ret.extend(
                    self._page_api(
                        self.spotify_svc.sp.playlist_items(playlist["id"])
                    )
                )

            return ret

    def _page_api(self, api_response: dict) -> dict:
        ret = api_response["items"]
        idx = 1
        while api_response["next"]:
            self._logger.debug(f"Sending Spotify API call {idx}")
            api_response = self.spotify_svc.sp.next(api_response)
            ret.extend(api_response["items"])
            idx += 1

        return ret

    @staticmethod
    def _to_spotify_song(api_songs: dict) -> List[SpotifySong]:
        ret = []
        for api_s in api_songs:
            s = SpotifySong()
            s.from_api(api_s)
            if s.is_valid():
                ret.append(s)

        return ret

    def is_playlist_owner(self, playlist: dict):
        user_id = self.spotify_svc.sp.current_user()["id"]
        return playlist["owner"]["id"] == user_id

    def _filter_playlists_by_owner(self, playlists):
        ret = {}
        for k, playlist in playlists.items():
            if self.is_playlist_owner(playlist):
                ret[k] = playlist
            else:
                self._logger.debug(
                    f'{playlist["name"]} is not owned by current user, skipping'
                )

        return ret
