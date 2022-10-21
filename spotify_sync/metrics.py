import base64
import inspect
import threading
import uuid
import requests
from datetime import datetime
from spotify_sync.common import hash_string

from spotify_sync.io_ import PersistentDataService

ACCESS_KEY = "b218dc01-d4b9-496f-99ac-249bd2a68397"
ENDPOINT = "https://api.spotify-sync.jbh.cloud/api/metrics"
DATA_SALT = "de084c0b-5053-4e6f-8fb7-7710af7f037f"


class MetricsService:
    def __init__(self, pd_svc: PersistentDataService):
        self.machine_id = pd_svc.get_anon_machine_id()
        self.execution_id = str(uuid.uuid4())
        self.config = pd_svc.config
        self.config_hash = hash_string(DATA_SALT, str(self.config.path))

    def notify(self, msg: str):
        try:
            run_source = inspect.stack()[3][3]
            if self.machine_id is not None:
                # dont wait for request
                threading.Thread(
                    target=self._post_data, args=(run_source, msg)
                ).start()
        except Exception:
            pass

    def _post_data(self, run_source: str, message: str = ""):
        try:
            execution_time = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            payload = {
                "machineId": self.machine_id,
                "runType": run_source,
                "runTypeAction": message,
                "executionTime": execution_time,
                "executionId": self.execution_id,
                "configHash": self.config_hash,
                "configMaxBitrate": self.config.data["DEEMIX_MAX_BITRATE"],
                "configSkipLowQuality": self.config.data[
                    "DEEMIX_SKIP_LOW_QUALITY"
                ],
                "configSpotifyPlaylistsEnabled": self.config.data[
                    "SPOTIFY_PLAYLISTS_ENABLED"
                ],
                "configSpotifyPlaylistsOwner": self.config.data[
                    "SPOTIFY_PLAYLISTS_OWNER_ONLY"
                ],
                "configPushover": self.config.data["PUSHOVER_ENABLED"],
                "configAutoscan": self.config.data["AUTOSCAN_ENABLED"],
            }

            req = requests.post(
                ENDPOINT
                + "?apikey="
                + base64.b64encode(
                    f'{ACCESS_KEY.replace("-", "+")}/{execution_time}'.encode(
                        "ascii"
                    )
                ).decode("utf-8"),
                json=payload,
            )
        except Exception:
            # Ignore any issues, do not interrupt running of app
            pass
