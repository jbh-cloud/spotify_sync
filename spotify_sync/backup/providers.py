import os
import sys
import hmac
import json
import shutil
import base64
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Union
from zipfile import ZipFile, ZIP_DEFLATED

# local imports
from spotify_sync.common import get_temp_dir
from spotify_sync.config import ConfigLoader, ConfigCache
from spotify_sync.dataclasses import BackupSnapshot, BackupManifest, Config
from spotify_sync.errors import RestoreZipNotExists
from spotify_sync.io_ import PersistentDataService

INTEGRITY_BLOB = "0563debb-4660-4696-b968-e282c68c568b"


class BackupProvider:
    def __init__(self, **kwargs):
        self.snapshot: Union[BackupSnapshot, None] = None

    def backup(self, **kwargs):
        pass

    def restore(self, **kwargs):
        pass

    def restore_zip_file(
        self,
        zip_file: Path,
        new_profile: Union[str, None] = None,
        overwrite_files=False,
    ):
        if not zip_file.exists() or not zip_file.is_file():
            raise RestoreZipNotExists

        try:
            temp = get_temp_dir()
            extract_dest = temp / zip_file.name
            extract_dest.mkdir(exist_ok=False)
            with ZipFile(zip_file, "r") as zipObj:
                zipObj.extractall(extract_dest)

            manifest = self._parse_manifest(extract_dest / ".manifest.json")
            if self._manifest_tampered(manifest):
                print("Backup has been manually tampered with, exiting..")
                sys.exit(1)

            snapshot = BackupSnapshot(
                manifest.profile,
                manifest.spotify_user,
                None,
                None,
                None,
                None,
                None,
            )

            if new_profile is not None:
                snapshot.profile = new_profile

            for f in extract_dest.glob("*.json"):
                if f.name == "config.json":
                    snapshot.config = f
                if f.name == "spotify.json":
                    snapshot.spotify = f
                if f.name == "processed.json":
                    snapshot.processed = f
                if f.name == "playlists.json":
                    snapshot.playlists = f
                if f.name == ".spotify-oauth.json":
                    snapshot.oauth = f

            if (
                snapshot.config is None
                or snapshot.spotify is None
                or snapshot.processed is None
            ):
                print(
                    "Mandatory files are not present in backup, unable to restore.."
                )
                sys.exit(1)

            self._restore_snapshot(snapshot, force=overwrite_files)
            print(
                f'Successfully restored persistent data for Spotify user "{snapshot.username}" from backup'
            )

        except Exception as ex:
            print(f"Failed restore, reason: {ex}")
            sys.exit(1)

        finally:
            try:
                shutil.rmtree(extract_dest)
            except UnboundLocalError:
                pass  # folder not created yet
            except Exception:
                print(
                    f"Failed to remove temp dir: {extract_dest}. Please clean this up manually."
                )

    @staticmethod
    def _restore_snapshot(snapshot, force=False) -> None:
        cc = ConfigCache()
        c_loader = ConfigLoader(config_file=Path(snapshot.config))
        config = Config(
            profile=None, path=snapshot.config, data=c_loader.load()
        )

        if snapshot.profile is not None:
            config.profile = snapshot.profile
            cc.add(snapshot.profile, snapshot.config, force=force)

        pd_svc = PersistentDataService(config)
        file_map = {}
        if snapshot.spotify is not None:
            file_map[snapshot.spotify] = pd_svc.get_spotify_songs_path()
        if snapshot.processed is not None:
            file_map[snapshot.processed] = pd_svc.get_processed_songs_path()
        if snapshot.playlists is not None:
            file_map[snapshot.playlists] = pd_svc.get_playlist_mapping_path()
        if snapshot.oauth is not None:
            file_map[snapshot.oauth] = pd_svc.get_spotify_oauth_path()

        for src, dest in file_map.items():
            if not dest.exists() or force:
                shutil.copy(src, dest)  # For Python 3.8+.
            else:
                print(
                    f"Skipping restore of {dest}, file exists and --force is not specified"
                )

    @staticmethod
    def _parse_manifest(file: Path) -> BackupManifest:
        if not file.exists() or not file.is_file():
            print(
                "Unable to find manifest in backup, are you use this is a spotify_sync backup?"
            )
            sys.exit(1)

        with open(file, mode="r", encoding="utf-8") as f:
            manifest = json.load(f, object_hook=lambda d: BackupManifest(**d))

        return manifest

    @staticmethod
    def _manifest_tampered(manifest: BackupManifest) -> bool:
        message = (manifest.spotify_user + manifest.timestamp).encode("utf-8")
        dig = hmac.new(
            INTEGRITY_BLOB.encode("utf-8"),
            msg=message,
            digestmod=hashlib.sha256,
        ).digest()
        should_match = base64.b64encode(dig).decode()
        return not manifest.checksum == should_match

    def add_files_to_zip(self, output_zip: Path) -> None:
        manifest = self._generate_manifest()

        with ZipFile(
            output_zip, "w", compression=ZIP_DEFLATED, compresslevel=9
        ) as zipObj:
            zipObj.write(self.snapshot.config, arcname="config.json")
            zipObj.write(self.snapshot.spotify, arcname="spotify.json")
            zipObj.write(self.snapshot.processed, arcname="processed.json")
            zipObj.write(self.snapshot.playlists, arcname="playlists.json")
            zipObj.write(self.snapshot.oauth, arcname=".spotify-oauth.json")
            zipObj.writestr(
                ".manifest.json",
                json.dumps(
                    manifest,
                    indent=4,
                    sort_keys=True,
                    default=lambda obj: obj.__dict__,
                ),
            )

    def _generate_manifest(self) -> BackupManifest:
        with open(self.snapshot.config, mode="r", encoding="utf-8") as f:
            config = json.load(f)

        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")
        username = config["spotify"]["username"]
        checksum = self._get_manifest_checksum(timestamp, username)

        return BackupManifest(
            profile=self.snapshot.profile,
            spotify_user=username,
            timestamp=timestamp,
            checksum=checksum,
        )

    @staticmethod
    def _get_manifest_checksum(timestamp, username):
        message = (username + timestamp).encode("utf-8")
        dig = hmac.new(
            INTEGRITY_BLOB.encode("utf-8"),
            msg=message,
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(dig).decode()  # py3k-mode


class FileSystemBackupProvider(BackupProvider):
    def __init__(self):
        super().__init__()

    def backup(self, out_dir: Union[str, None], snapshot: BackupSnapshot):
        self.snapshot = snapshot
        try:
            export_fn = (
                Path(os.getcwd()) if out_dir is None else Path(out_dir)
            ) / (
                "spotify_sync_backup_"
                + datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")
                + ".zip"
            )
            self.add_files_to_zip(export_fn)
            print(f"Successfully backed up. {export_fn}")
            sys.exit(0)
        except Exception as ex:
            print(f"Failed creating backup, error was: {ex}")
            sys.exit(1)

    def restore(
        self, zip_file: Path, force=False, new_profile=Union[str, None]
    ):
        self.restore_zip_file(
            zip_file, overwrite_files=force, new_profile=new_profile
        )
