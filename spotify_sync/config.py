import os
import shutil
import sys
import json
import psutil
import jsonschema
from pathlib import Path
from flatdict import FlatDict
from datetime import datetime
from tabulate import tabulate
from typing import List, Union
from jsonschema import validate
from pkg_resources import resource_stream

# local imports
from spotify_sync.appdirs_ import CONFIG
from spotify_sync.common import dump_json, load_json
from spotify_sync.dataclasses import ConfigProfile, Config
from spotify_sync.errors import JsonSchemaInvalid
from spotify_sync.io_ import PersistentDataService

current_schema = json.load(
    resource_stream("spotify_sync", "data/config_schema.json")
)
legacy_schema = json.load(
    resource_stream("spotify_sync", "data/config_schema_legacy.json")
)
config_example = json.load(
    resource_stream("spotify_sync", "data/config.json.example")
)

cfg = None


class ConfigCache:
    def __init__(self):
        self.root: Path = Path(CONFIG)
        self.cache_manifest = self.root / ".profiles.json"
        self.profiles: List[ConfigProfile] = []
        self._init_cache_manifest()
        self._discover_cached_profiles()

    def get(self, name: str) -> Union[ConfigProfile, None]:
        self._discover_cached_profiles()
        return self._get_profile(name)

    def get_path(self, name: str) -> Union[Path, None]:
        for p in self.profiles:
            if p.name == name:
                return p.path

        return None

    def add(self, name: str, path: str, force=False) -> None:
        if " " in name:
            print("Profile must not contain spaces!")
            sys.exit(1)

        lookup_profile = self._get_profile(name)
        if lookup_profile is not None and not force:
            print(f'Profile "{name}" already exists!')
            sys.exit(0)

        c_loader = ConfigLoader(config_file=Path(path))
        if not c_loader.is_valid:
            print(f"Config validation error: {c_loader.validation_msg}")
            print(
                "Please review: https://docs.spotify-sync.jbh.cloud/configuration/schema"
            )
            sys.exit(1)

        # copy config to correct location
        dest = self.root / f"{name}.json"
        shutil.copyfile(path, dest)

        profile = ConfigProfile(name=name, path=dest)
        self.profiles.append(profile)
        self._persist_cache_manifest()

        print(f'Successfully added "{name}" to the config cache')

    def remove(self, name: str) -> None:
        profile = self._get_profile(name)
        if profile is None:
            print(f"{name} does not exist!")
            return

        profile.path.unlink()
        self.profiles.remove(profile)
        self._persist_cache_manifest()
        print(f'Successfully removed "{name}" from the config cache')

    def list(self) -> None:
        summary_data = []
        for p in self.profiles:
            c_loader = ConfigLoader(profile=p)
            conf = c_loader.load()

            summary_data.append(
                [
                    p.name,
                    conf["SPOTIFY_USERNAME"],
                    conf["SPOTIFY_PLAYLISTS_ENABLED"],
                    conf["DEEMIX_DOWNLOAD_PATH"],
                    conf["DEEMIX_MAX_BITRATE"],
                    conf["DEEMIX_SKIP_LOW_QUALITY"],
                    conf["DEEMIX_STRICT_MATCHING"],
                ]
            )

        headers = [
            "profile",
            "spotify_user",
            "playlists",
            "download_path",
            "max_bitrate",
            "skip_low_quality",
            "strict_matching",
        ]

        print()
        print(tabulate(summary_data, headers))
        print()

    def list_paths(self) -> None:
        headers = ["profile", "last_modified", "config", "persistent_data"]
        summary_data = []
        for p in self.profiles:
            c_loader = ConfigLoader(profile=p)
            conf = c_loader.load()
            pd_root = PersistentDataService(
                Config(p.name, p.path, conf)
            ).user_root
            summary_data.append(
                [
                    p.name,
                    datetime.fromtimestamp(p.path.lstat().st_mtime).strftime(
                        "%Y-%m-%dT%H%M%S"
                    ),
                    p.path,
                    pd_root,
                ]
            )

        print()
        print(tabulate(summary_data, headers))
        print()

    def generate(self) -> None:
        config_fn = self._get_non_existent_config_fn()
        dump_json(config_fn, config_example, sort_keys=False)
        print(f"Generated example config file: {config_fn}")

    def _discover_cached_profiles(self) -> None:
        self.profiles = []

        manifest_profiles = load_json(self.cache_manifest)
        for name, path in manifest_profiles.items():
            self.profiles.append(ConfigProfile(name, Path(path)))

    def _add_profile(self, name: str, path: Path) -> None:
        source = load_json(path)
        profile = self.root / f"{name}.json"
        dump_json(profile, source)
        self._persist_cache_manifest()

    def _get_profile(self, name) -> Union[ConfigProfile, None]:
        for p in self.profiles:
            if p.name != name:
                continue
            return p
        return None

    def _get_config(self, profile_name: str) -> Union[dict, None]:
        profile = self._get_profile(profile_name)
        if profile is None:
            return None

        return load_json(profile.path)

    @staticmethod
    def _get_non_existent_config_fn() -> Path:
        w_dir = Path(os.getcwd())
        config_file = Path(w_dir / "config.json")

        while config_file.exists():
            parts = config_file.name.split(".")
            if len(parts) == 3:
                i = int(parts[1]) + 1
                config_file = Path(
                    w_dir / (parts[0] + f".{str(i)}." + parts[2])
                )
            else:
                config_file = Path(w_dir / (parts[0] + ".1." + parts[1]))

        return config_file

    def _init_cache_manifest(self) -> None:
        if not self.cache_manifest.exists():
            dump_json(self.cache_manifest, {}, hidden=True)

    def _persist_cache_manifest(self) -> None:
        manifest = {}
        for p in self.profiles:
            manifest[p.name] = str(p.path)

        dump_json(self.cache_manifest, manifest, hidden=True)


class ConfigLoader:
    def __init__(
        self,
        profile: ConfigProfile = None,
        config_file: Path = None,
        legacy_mode=False,
    ):
        self.profile = profile
        self.config_file = config_file
        self.legacy_mode = legacy_mode
        self.is_valid = False
        self.validation_msg = ""
        self._config = {}
        self._load_config()

    def load(self, flatten_settings=True) -> dict:
        if flatten_settings:
            return self._flatten_settings(self._config)
        else:
            return self._config

    def migrate_from_legacy_schema(self) -> dict:
        if not self.is_valid:
            raise JsonSchemaInvalid

        config = config_example

        config["threads"] = self._config["threads"]
        config["anon_metrics_enable"] = True
        config["deemix"]["arl"] = self._config["deemix"]["arl"]
        config["deemix"]["download_path"] = self._config["deemix"][
            "download_path"
        ]
        config["deemix"]["max_bitrate"] = self._config["deemix"]["max_bitrate"]
        config["deemix"]["skip_low_quality"] = self._config["deemix"][
            "skip_low_quality"
        ]
        config["spotify"]["client_id"] = self._config["spotify"]["client_id"]
        config["spotify"]["client_secret"] = self._config["spotify"][
            "client_secret"
        ]
        config["spotify"]["username"] = self._config["spotify"]["username"]
        config["spotify"]["scope"] = self._config["spotify"]["scope"]
        config["spotify"]["redirect_uri_port"] = self._config["spotify"][
            "redirect_uri_port"
        ]
        config["spotify"]["playlists"]["enabled"] = self._config["spotify"][
            "playlists"
        ]["enabled"]
        config["spotify"]["playlists"]["excluded"] = self._config["spotify"][
            "playlists"
        ]["excluded"]
        config["pushover"]["enabled"] = self._config["pushover"]["enabled"]
        config["pushover"]["user_key"] = self._config["pushover"]["user_key"]
        config["pushover"]["api_token"] = self._config["pushover"]["api_token"]
        config["autoscan"]["enabled"] = self._config["autoscan"]["enabled"]
        config["autoscan"]["endpoint"] = self._config["autoscan"]["endpoint"]
        config["autoscan"]["auth_enabled"] = self._config["autoscan"][
            "auth_enabled"
        ]
        config["autoscan"]["username"] = self._config["autoscan"]["username"]
        config["autoscan"]["password"] = self._config["autoscan"]["password"]

        self.legacy_mode = False
        self._validate(config)

        if self.is_valid:
            return config
        else:
            print("Migrated config did not meet the new schema.")
            print(f"Validation error: {self.validation_msg}")
            print(f"Config dump -> {json.dumps(config, indent=True)}")
            sys.exit(1)

    def _load_config(self) -> None:
        if self.profile is None and self.config_file is None:
            raise Exception(
                "Must either specify a config file or config profile!"
            )

        if self.profile is not None:
            config_path = self.profile.path
            validation_msg_error = (
                f"Config for profile {self.profile.name} is not valid"
            )
        else:
            config_path = self.config_file
            validation_msg_error = (
                f"Config file is not valid: {self.config_file}"
            )

        with open(config_path, mode="r", encoding="utf-8") as f:
            self._config = json.load(f)

        self._validate(self._config)
        if not self.is_valid and not self._try_auto_update_config():
            print(validation_msg_error)
            print(f"Validation error: {self.validation_msg}")
            print(
                "Please review: https://docs.spotify-sync.jbh.cloud/configuration/schema"
            )
            sys.exit(1)

        self._parse_threads()

    def _parse_threads(self) -> None:
        # Ensure key case correct
        self._config = {k.lower(): v for k, v in self._config.items()}

        machine_threads = psutil.cpu_count()
        if self._config["threads"] == -1:
            threads = machine_threads
        else:
            threads = (
                self._config["threads"]
                if self._config["threads"] <= machine_threads
                else machine_threads
            )

        self._config["threads"] = threads

    def _validate(self, config):
        schema = current_schema if not self.legacy_mode else legacy_schema
        try:
            validate(instance=config, schema=schema)
            self.is_valid = True
        except jsonschema.exceptions.ValidationError as err:
            self.validation_msg = err.message

    @staticmethod
    def _flatten_settings(data: dict) -> dict:
        return {
            k.upper(): v
            for k, v in dict(FlatDict(data, delimiter="_")).items()
        }

    def _try_auto_update_config(self) -> bool:
        updated_config = auto_update_config(self._config)
        self._validate(updated_config)
        if self.is_valid:
            self._config = updated_config
            dump_json(self.config_file or self.profile.path, self._config)
            return True


def auto_update_config(config: dict) -> dict:
    c = config.copy()
    try:
        if c.get("anon_metrics_enable") is None:
            c["anon_metrics_enable"] = False

        if c["spotify"].get("custom_application") is None:
            c["spotify"]["custom_application"] = {
                "enabled": True,
                "client_id": c["spotify"]["client_id"],
                "client_secret": c["spotify"]["client_secret"],
                "scope": c["spotify"]["scope"],
                "redirect_uri_port": c["spotify"]["redirect_uri_port"],
            }

            del c["spotify"]["client_id"]
            del c["spotify"]["client_secret"]
            del c["spotify"]["scope"]
            del c["spotify"]["redirect_uri_port"]

        if isinstance(c["threads"], str):
            try:
                c["threads"] = int(c["threads"])
            except ValueError:
                # Unable to parse threads from str, using all available
                c["threads"] = -1

        return c
    except Exception:
        return config


def load() -> Config:
    global cfg
    if cfg is None:
        if os.environ.get("MANUAL_CONFIG_FILE") is not None:
            cl = ConfigLoader(
                config_file=Path(os.environ["MANUAL_CONFIG_FILE"])
            )
            cfg = Config(path=cl.config_file, data=cl.load(), profile=None)
        elif os.environ.get("CONFIG_PROFILE") is not None:
            cc = ConfigCache()
            profile = cc.get(os.environ["CONFIG_PROFILE"])

            if profile is None:
                print(
                    f'No profile found with name: {os.environ["CONFIG_PROFILE"]}'
                )
                sys.exit(1)

            cfg = Config(
                path=profile.path,
                data=ConfigLoader(profile=profile).load(),
                profile=profile.name,
            )
            os.environ["LOG_PATH"] = str(
                PersistentDataService(cfg).get_log_path()
            )
        else:
            raise Exception(
                "Must load config with either a config file or config profile"
            )

    return cfg


def set_env(input_value: str, env_name: str) -> None:
    if input_value is not None:
        os.environ[env_name] = input_value
