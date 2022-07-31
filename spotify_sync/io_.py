import json
from pathlib import Path
from typing import Dict

# local imports
from spotify_sync.appdirs_ import DATA
from spotify_sync.config import Config
from spotify_sync.dataclasses import SpotifySong, ProcessedSong, BackupSnapshot
from spotify_sync.common import load_json, dump_json, as_spotify_song, as_processed_song
from spotify_sync.errors import SnapshotFileNotExists


class PersistentDataService:
    def __init__(self, app_config: Config):
        self.config = app_config
        self.root: Path = self._ensure_root_dir(app_config)

    def verify_files(self):
        files = [self.get_spotify_songs_path(), self.get_processed_songs_path()]

        for f in files:
            if not Path(f).is_file():
                with open(f, mode="w", encoding="utf-8") as fp:
                    json.dump({}, fp)

    def load_spotify_songs(self) -> Dict[str, SpotifySong]:
        file = self.get_spotify_songs_path()
        return as_spotify_song(load_json(file))

    def load_processed_songs(self) -> Dict[str, ProcessedSong]:
        file = self.get_processed_songs_path()
        return as_processed_song(load_json(file))

    def persist_spotify_songs(self, songs) -> None:
        file = self.get_spotify_songs_path()
        file.parent.mkdir(exist_ok=True)
        dump_json(file, songs)

    def persist_processed_songs(self, songs) -> None:
        file = self.get_processed_songs_path()
        file.parent.mkdir(exist_ok=True)
        dump_json(file, songs)

    def get_spotify_oauth(self):
        return self.get_spotify_oauth_path()

    def gather_snapshot_files(self) -> BackupSnapshot:
        snapshot = BackupSnapshot(
            profile=self.config.profile,
            username=self.config.data["SPOTIFY_USERNAME"],
            config=self.config.path,
            spotify=self.get_spotify_songs_path(),
            processed=self.get_processed_songs_path(),
            playlists=self.get_playlist_mapping_path(),
            oauth=self.get_spotify_oauth_path(),
        )

        # TODO: Allow partial backup and restore
        kill = False
        if not snapshot.config.exists():
            print(f"Cannot find config file: {snapshot.config}")
            kill = True
        if not snapshot.spotify.exists():
            print(f"Cannot find spotify songs file: {snapshot.spotify}")
            kill = True
        if not snapshot.processed.exists():
            print(f"Cannot find processed songs file: {snapshot.processed}")
            kill = True
        if not snapshot.playlists.exists():
            print(f"Cannot find playlists file: {snapshot.playlists}")
            kill = True
        if not snapshot.oauth.exists():
            print(f"Cannot find spotify oauth cache file: {snapshot.oauth}")
            kill = True

        if kill:
            raise SnapshotFileNotExists

        return snapshot

    def get_spotify_songs_path(self) -> Path:
        return self.root / f'spotify-{self.config.data["SPOTIFY_USERNAME"]}.json'

    def get_processed_songs_path(self) -> Path:
        return self.root / f'processed-{self.config.data["SPOTIFY_USERNAME"]}.json'

    def get_playlist_mapping_path(self) -> Path:
        return (
            self.root / f'playlist-mapping-{self.config.data["SPOTIFY_USERNAME"]}.json'
        )

    def get_spotify_oauth_path(self) -> Path:
        return (
            self.root / f'.spotify-oauth-cache-{self.config.data["SPOTIFY_USERNAME"]}'
        )

    def get_log_path(self) -> Path:
        return self.root / "logs" / "spotify_sync.log"

    def persist_playlist_mapping(self, mapping):
        file = Path(self.get_playlist_mapping_path())
        dump_json(file, mapping)

    @staticmethod
    def _ensure_root_dir(config: Config) -> Path:
        if config.profile is not None:
            root = Path(DATA) / (config.data["SPOTIFY_USERNAME"] + f"_{config.profile}")
        else:
            root = Path(DATA) / config.data["SPOTIFY_USERNAME"]

        root.mkdir(parents=True, exist_ok=True)
        return root
