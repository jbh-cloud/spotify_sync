import json
import os, sys
import jsonschema
from jsonschema import validate

# local imports
from src.log import rootLogger

logger = rootLogger.getChild('CONFIG')
cfg = None


schema = """
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "threads": {
      "type": "string"
    },
    "deemix": {
      "type": "object",
      "properties": {
        "arl": {
          "type": "string"
        },
        "download_path": {
          "type": "string"
        },
        "max_bitrate": {
          "type": "string"
        },
        "skip_low_quality": {
          "type": "boolean"
        }
      },
      "required": [
        "arl",
        "download_path",
        "max_bitrate",
        "skip_low_quality"
      ]
    },
    "logging": {
      "type": "object",
      "properties": {
        "level": {
          "type": "string"
        },
        "path": {
          "type": "string"
        }
      },
      "required": [
        "level",
        "path"
      ]
    },
    "spotify": {
      "type": "object",
      "properties": {
        "client_id": {
          "type": "string"
        },
        "client_secret": {
          "type": "string"
        },
        "username": {
          "type": "string"
        },
        "scope": {
          "type": "string"
        },
        "redirect_uri_port": {
          "type": "string"
        },
        "playlists": {
          "type": "object",
          "properties": {
            "enabled": {
              "type": "boolean"
            },
            "excluded": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "required": [
            "enabled",
            "excluded"
          ]
        }
      },
      "required": [
        "client_id",
        "client_secret",
        "username",
        "scope",
        "redirect_uri_port",
        "playlists"
      ]
    },
    "pushover": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean"
        },
        "user_key": {
          "type": "string"
        },
        "api_token": {
          "type": "string"
        }
      },
      "required": [
        "enabled",
        "user_key",
        "api_token"
      ]
    },
    "autoscan": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean"
        },
        "endpoint": {
          "type": "string"
        },
        "auth_enabled": {
          "type": "boolean"
        },
        "username": {
          "type": "string"
        },
        "password": {
          "type": "string"
        }
      },
      "required": [
        "enabled",
        "endpoint",
        "auth_enabled",
        "username",
        "password"
      ]
    },
    "git": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean"
        }
      },
      "required": [
        "enabled"
      ]
    },
    "data": {
      "type": "object",
      "properties": {
        "persistent_data_root": {
          "type": "string"
        },
        "files": {
          "type": "object",
          "properties": {
            "liked_songs": {
              "type": "string"
            },
            "processed_songs": {
              "type": "string"
            },
            "playlist_mapping": {
              "type": "string"
            }
          },
          "required": [
            "liked_songs",
            "processed_songs",
            "playlist_mapping"
          ]
        }
      },
      "required": [
        "persistent_data_root",
        "files"
      ]
    }
  },
  "required": [
    "threads",
    "deemix",
    "logging",
    "spotify",
    "pushover",
    "autoscan",
    "git",
    "data"
  ]
}
"""


class Configuration:
    def __init__(self):
        self.config = {}
        self._load_config()

    def _load_config(self):
        logger.debug(f'Loading config')
        loaded = self._load_config_file()
        self._validate(loaded)
        self.config = self._flatten_settings(loaded)

    @staticmethod
    def _validate(config):
        logger.debug('Validating config against JSON Schema')
        try:
            validate(instance=config, schema=json.loads(schema))
        except jsonschema.exceptions.ValidationError as err:
            logger.error(f'Failed to validate config file against schema, error was: {err.message}')
            sys.exit(1)

    @staticmethod
    def _load_config_file():
        file = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        if not os.path.isfile(file):
            logger.error(f'Unable to find config file at: {file}')
            sys.exit(1)

        try:
            with open(os.path.join(file), mode='r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as ex:
            logger.error(f'Failed to open config file {file}, exception was: ', ex)
            sys.exit(1)

    @staticmethod
    def _flatten_settings(settings: dict):
        logger.debug(f'Flattening settings from nested dictionary')
        ret = {}
        for k in settings.keys():
            if isinstance(settings[k], dict):
                for k2 in settings[k].keys():
                    if isinstance(settings[k][k2], dict):
                        for k3 in settings[k][k2].keys():
                            value = settings[k][k2][k3]
                            ret["_".join([k.upper(), k2.upper(), k3.upper()])] = value
                    else:
                        value = settings[k][k2]
                        ret["_".join([k.upper(), k2.upper()])] = value
            else:
                ret[k.upper()] = settings[k]
        return ret


def load():
    global cfg
    if cfg is None:
        cfg = Configuration().config
        os.environ["SPOTIFY_SYNC_LOG_LEVEL"] = cfg["LOGGING_LEVEL"]
        os.environ["SPOTIFY_SYNC_LOG_PATH"] = cfg["LOGGING_PATH"]

    return cfg