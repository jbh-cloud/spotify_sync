# defer imports due to click cli speed implications

import sys

from spotify_sync.common import get_temp_fn, dump_json
from spotify_sync.dataclasses import Config


class SpotifySyncApp:
    def __init__(self):
        from spotify_sync.config import ConfigCache

        self.config: Config = None
        self.cc = ConfigCache()
        self._metrics = None
        self._logger = None
        self.pushover = None

    def authorize_spotify(self):
        from spotify_sync.io_ import PersistentDataService
        from spotify_sync.spotify_ import SpotifyService

        self._setup(logger=False)

        pd_svc = PersistentDataService(self.config)
        spotify_svc = SpotifyService(self.config, pd_svc)

        spotify_svc.cache_spotify_auth()
        print("Successfully cached Spotify OAuth token!")

    def auto(self):
        from spotify_sync.io_ import PersistentDataService
        from spotify_sync.spotify_ import SpotifyService
        from spotify_sync.match import MatchService
        from spotify_sync.autoscan_ import AutoScanService
        from spotify_sync.download import DownloadService

        self._setup()

        self.log("Script started with auto command")
        self.pushover.send_message("auto started")

        pd_svc = PersistentDataService(self.config)
        spotify_svc = SpotifyService(self.config, pd_svc)
        match_svc = MatchService(self.config, pd_svc)
        download_svc = DownloadService(self.config, pd_svc, self.pushover)
        autoscan_svc = AutoScanService(self.config)

        # Checks
        download_svc.preflight()

        spotify_svc.sync()
        match_svc.process_spotify()
        download_svc.download_missing_tracks()
        autoscan_svc.scan(download_svc.downloaded_song_paths)

        if len(download_svc.downloaded_song_paths) >= 1:
            self.pushover.send_message(
                f"Successfully downloaded {len(download_svc.downloaded_song_paths)} new songs(s)"
            )

        self.pushover.send_message("auto finished")
        self.log("Script finished")
        sys.exit(0)

    def sync_spotify(self):
        from spotify_sync.io_ import PersistentDataService
        from spotify_sync.spotify_ import SpotifyService

        self._setup()

        self.log("Script started with sync-spotify command")
        self.pushover.send_message("sync-spotify started")

        pd_svc = PersistentDataService(self.config)
        spotify_svc = SpotifyService(self.config, pd_svc)

        spotify_svc.sync()

        self.pushover.send_message("sync-spotify finished")
        self.log("Script finished")
        sys.exit(0)

    def match_spotify(self):
        from spotify_sync.io_ import PersistentDataService
        from spotify_sync.match import MatchService

        self._setup()

        self.log("Script started with match-spotify command")
        self.pushover.send_message("match-spotify started")

        pd_svc = PersistentDataService(self.config)
        match_svc = MatchService(self.config, pd_svc)

        match_svc.process_spotify()

        self.pushover.send_message("match-spotify finished")
        self.log("Script finished")
        sys.exit(0)

    def download_missing(self):
        from spotify_sync.io_ import PersistentDataService
        from spotify_sync.download import DownloadService

        self._setup()

        self.log("Script started with download-missing command")
        self.pushover.send_message("download-missing started")

        pd_svc = PersistentDataService(self.config)
        download_svc = DownloadService(self.config, pd_svc, self.pushover)

        # Checks
        download_svc.preflight()

        download_svc.download_missing_tracks()

        self.pushover.send_message("download-missing finished")
        self.log("Script finished")
        sys.exit(0)

    def scan(self, paths):
        from spotify_sync.autoscan_ import AutoScanService

        self._setup()

        self._logger.info("Script started with manual-scan command")

        autoscan_svc = AutoScanService(self.config)
        autoscan_svc.scan(paths)

        self._logger.info("Script finished")

    def playlist_stats(self):
        from spotify_sync.io_ import PersistentDataService
        from spotify_sync.spotify_ import SpotifyService

        self._setup(logger=False)

        pd_svc = PersistentDataService(self.config)
        spotify_svc = SpotifyService(self.config, pd_svc)

        spotify_svc.display_playlist_stats()

    def validate_downloaded_files(self):
        pass
        # from spotify_sync.io_
        #
        # self._logger.info('Script started with validate-downloaded-files command')
        # missing = io_.get_missing_files()
        # self._logger.info(f'Found {str(missing)} missing songs')
        # self._logger.info('Script finished')

    def failed_download_stats(self):
        from spotify_sync.io_ import PersistentDataService
        from spotify_sync.download import DownloadService
        from spotify_sync.pushover_ import PushoverClient

        self._setup(logger=False)

        pd_svc = PersistentDataService(self.config)
        DownloadService(
            self.config, pd_svc, PushoverClient()
        ).display_failed_download_stats()

    def cache_config_profile(self, name, path):
        self.cc.add(name, path)

    def remove_config_profile(self, name):
        self.cc.remove(name)

    def list_config_profiles(self):
        self.cc.list()

    def list_config_profile_paths(self):
        self.cc.list_paths()

    def generate_example_config(self):
        self.cc.generate()

    @staticmethod
    def migrate_config():
        import os
        from pathlib import Path

        from spotify_sync.config import ConfigLoader

        if os.environ.get("MANUAL_CONFIG_FILE") is None:
            print("Must provide a config file to migrate")
            sys.exit(1)

        cl = ConfigLoader(
            config_file=Path(os.environ["MANUAL_CONFIG_FILE"]),
            legacy_mode=True,
        )
        new_config = cl.migrate_from_legacy_schema()

        output = Path(os.getcwd()) / get_temp_fn(extension=".json")
        dump_json(output, new_config)
        print(f"Successfully migrated config -> {output}")

    @staticmethod
    def migrate_to_profile(spotify, processed, profile_name, config_is_legacy):
        import shutil
        import json
        import os
        from pathlib import Path

        from spotify_sync.dataclasses import Config
        from spotify_sync.io_ import PersistentDataService
        from spotify_sync.config import ConfigLoader, ConfigCache
        from spotify_sync.common import get_temp_file

        if os.environ.get("MANUAL_CONFIG_FILE") is None:
            print("Must provide a config file to migrate")
            sys.exit(1)

        cfg_file = Path(os.environ["MANUAL_CONFIG_FILE"])

        cc = ConfigCache()
        cl = ConfigLoader(config_file=cfg_file, legacy_mode=config_is_legacy)

        if config_is_legacy:
            config = cl.migrate_from_legacy_schema()
            cfg_file = get_temp_file()
            with open(cfg_file, mode="w", encoding="utf-8") as f:
                json.dump(config, f)

        cc.add(profile_name, cfg_file)
        profile = cc.get(profile_name)

        pd_svc = PersistentDataService(
            Config(path=profile.path, data=cl.load(), profile=profile.name)
        )

        # TODO: handle path already exist
        shutil.copy(spotify, pd_svc.get_spotify_songs_path())
        shutil.copy(processed, pd_svc.get_processed_songs_path())

        if config_is_legacy:
            cfg_file.unlink()

        print(f'Migrated files successfully to profile "{profile_name}"')

    def local_backup(self, out_dir: str):
        from spotify_sync.errors import SnapshotFileNotExists
        from spotify_sync.io_ import PersistentDataService
        from spotify_sync.backup.providers import FileSystemBackupProvider

        self._setup(logger=False)

        try:
            snapshot = PersistentDataService(
                self.config
            ).gather_snapshot_files()
            provider = FileSystemBackupProvider()
            provider.backup(out_dir, snapshot)
        except SnapshotFileNotExists:
            print(
                "Failed local backup - One or more required snapshot files do not exist!"
            )
            sys.exit(1)
        except Exception:
            raise

    def log(self, message):
        print(message) if self._logger is None else self._logger.info(message)
        if self.config is not None and self._metrics is not None:
            self._metrics.notify(message)

    @staticmethod
    def local_restore(zip_file: str, force: bool, new_profile: str):
        from pathlib import Path
        from spotify_sync.errors import RestoreZipNotExists
        from spotify_sync.backup.providers import FileSystemBackupProvider

        try:
            provider = FileSystemBackupProvider()
            provider.restore(
                zip_file=Path(zip_file), force=force, new_profile=new_profile
            )
        except RestoreZipNotExists:
            print(f'Specified zip to restore does not exist: "{zip_file}"')
            sys.exit(1)
        except Exception:
            raise

    def _notify_user_config(self):
        self._logger.info(
            f"Loading config from profile: {self.config.profile}"
        ) if self.config.profile is not None else self._logger.info(
            f"Loading config from file {self.config.path}"
        )

    def _load_config(self):
        from spotify_sync.config import load as load_config

        self.config = load_config()

    def _setup_logger(self):
        from spotify_sync.log import get_logger

        self._logger = get_logger().getChild("SpotifySync")

    def _setup(self, logger=True):
        from spotify_sync.pushover_ import PushoverClient

        self._load_config()
        if logger:
            self._setup_logger()
            self._setup_metrics_if_enabled(self.config)
            self.pushover = PushoverClient(self.config)
            self._notify_user_config()

    def _setup_metrics_if_enabled(self, config: Config):
        from spotify_sync.metrics import MetricsService
        from spotify_sync.io_ import PersistentDataService

        if config.data["ANON_METRICS_ENABLE"]:
            self._metrics = MetricsService(PersistentDataService(config))
