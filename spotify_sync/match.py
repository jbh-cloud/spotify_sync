from typing import Dict
import deezer as Deezer
from deezer.errors import DataException
from concurrent.futures import ThreadPoolExecutor, wait

# local imports
from spotify_sync.dataclasses import Config
from spotify_sync.io_ import PersistentDataService
from spotify_sync.dataclasses import ProcessedSong, SpotifySong

# load Deezer (for matches), API is unauthenticated
client = Deezer.Deezer()


class MatchLogger:
    def __init__(self, song: SpotifySong):
        from spotify_sync.log import get_logger

        self._logger = get_logger().getChild("Match")
        self._song = song

    def info(self, message: str):
        self._logger.info(
            f"[{self._song.artist} - {self._song.title}] - {message}"
        )

    def warning(self, message: str):
        self._logger.warning(
            f"[{self._song.artist} - {self._song.title}] - {message}"
        )

    def debug(self, message: str):
        self._logger.debug(
            f"[{self._song.artist} - {self._song.title}] - {message}"
        )

    def error(self, message: str):
        self._logger.error(
            f"[{self._song.artist} - {self._song.title}] - {message}"
        )


class SongMatcher:
    def __init__(self, song: SpotifySong):
        self._logger = MatchLogger(song)
        self.song = song
        self.match = False
        self.match_type = None
        self.match_message = None
        self.match_payload = None

    def _match_via_isrc(self):
        track = Deezer.API.get_track(client.api, f"isrc:{self.song.isrc}")

        self._logger.debug("Matched - [isrc]")
        self.match = True
        self.match_type = "isrc"
        self.match_payload = track

    def _match_fuzzy(self):
        deezer_search = Deezer.API.advanced_search(
            client.api,  # self
            self.song.artist,  # artist
            self.song.album,  # album
            self.song.title,  # track name
        )

        if len(deezer_search["data"]) > 0:
            self._logger.debug("Matched - [fuzzy]")
            self.match = True
            self.match_type = "fuzzy"
            self.match_payload = deezer_search["data"][0]
        else:
            self._logger.debug(
                f"Failed fuzzy searching, SpotifyId: {self.song.id_}"
            )

    def search(self):
        try:
            self._match_via_isrc()
        except DataException:
            self._match_fuzzy()
        except Exception as ex:
            raise Exception(ex)

        if self.match:
            if "link" not in self.match_payload:
                self._logger.warning(
                    f"[SpotifyId:{self.song.id_}] - Matched but response does not contain a Deezer link, unmatching.."
                )
                self.match = False
                self.match_message = (
                    "Matched but response does not contain a Deezer link"
                )
                return

            if self.match_payload.get(
                "artist"
            ) is not None and not self.match_payload["artist"].get("name"):
                self._logger.warning(
                    f"[SpotifyId:{self.song.id_}] - Matched but response does not contain an Deezer artist, unmatching.."
                )
                self.match = False
                self.match_message = f"Matched but response does not contain a artist name, likely this link will not work. Matched link: '{self.match_payload['link']}'"
                return

            if "id" not in self.match_payload:
                self._logger.warning(
                    f"[SpotifyId:{self.song.id_}] - Matched but response does not contain a Deezer id, unmatching.."
                )
                self.match = False
                self.match_message = (
                    "Matched but response does not contain a Deezer id"
                )


class MatchService:
    def __init__(self, app_config: Config, pd_svc: PersistentDataService):
        from spotify_sync.log import get_logger

        self._logger = get_logger().getChild("MatchService")
        self.config = app_config
        self.pd_svc = pd_svc
        self.spotify: Dict[str, SpotifySong] = {}
        self.processed: Dict[str, ProcessedSong] = {}
        self.unprocessed: Dict[str, SpotifySong] = {}
        self.matched_count = 0

    def process_spotify(self):
        self.pd_svc.verify_files()
        self._refresh_files()
        self._match_unprocessed()
        self.pd_svc.persist_processed_songs(self.processed)

    def _refresh_files(self):
        self.spotify = self.pd_svc.load_spotify_songs()
        self.processed = self.pd_svc.load_processed_songs()
        self.unprocessed = self._get_unprocessed_songs()

    def _get_unprocessed_songs(self) -> Dict[str, SpotifySong]:
        self.unprocessed = {}
        for k in self.spotify:
            if k not in self.processed:
                self.unprocessed[k] = self.spotify[k]

        return self.unprocessed

    def _process_match(self, matcher: SongMatcher) -> bool:
        if matcher.match:
            if "link" not in matcher.match_payload:
                self._logger.warning(
                    f"[SpotifyId:{matcher.song.id_}] - Matched but response does not contain a Deezer link, unmatching.."
                )
                matcher.match = False
                matcher.match_message = (
                    "Matched but response does not contain a Deezer link"
                )

        s = ProcessedSong(
            spotify_title=matcher.song.title,
            spotify_artist=matcher.song.artist,
            spotify_isrc=matcher.song.isrc,
            spotify_url=matcher.song.url,
            spotify_id=matcher.song.id_,
            deezer_title=matcher.match_payload["title"]
            if matcher.match
            else None,
            deezer_artist=matcher.match_payload["artist"]["name"]
            if matcher.match
            else None,
            # deezer fuzzy search payload doesnt return isrc of matched item
            deezer_isrc=matcher.match_payload.get("isrc")
            if matcher.match
            else None,
            deezer_url=matcher.match_payload["link"]
            if matcher.match
            else None,
            deezer_id=matcher.match_payload["id"] if matcher.match else None,
            matched=matcher.match,
            match_type=matcher.match_type,
            match_message=matcher.match_message,
            match_pending_download=matcher.match,
        )

        self.processed[s.spotify_id] = s
        return s.matched

    def _match_unprocessed(self):
        msg = f"Attempting to match {len(self.unprocessed)} Spotify songs to Deezer"
        if len(self.unprocessed) > 500:
            msg = msg + ", this could take some time.."

        self._logger.info(msg)

        matchers = [
            SongMatcher(song=song) for song in self.unprocessed.values()
        ]
        with ThreadPoolExecutor(self.config.data["THREADS"]) as executor:
            match_futures = [executor.submit(m.search()) for m in matchers]
            wait(match_futures)

        for m in matchers:
            if self._process_match(m):
                self.matched_count += 1

        self._logger.info(
            f"Matched {self.matched_count}/{len(self.unprocessed)} new liked song(s)"
        )

    def _save_processed(self):
        self._logger.debug(
            f"Serializing {str(len(self.processed))} processed songs back to disk"
        )
        self.pd_svc.persist_processed_songs(self.processed)
