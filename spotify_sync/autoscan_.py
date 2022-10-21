import requests
from pathlib import Path

# local imports
from spotify_sync.config import Config


class AutoScanService:
    def __init__(self, app_config: Config):
        from spotify_sync.log import get_logger

        self._logger = get_logger().getChild("AutoScanService")
        self.config = app_config

    def scan(self, paths):
        if self.config.data["AUTOSCAN_ENABLED"]:
            unique = set()
            for p in paths:
                if Path(p).is_file():
                    p = Path(p).parent
                unique.add(p)

            for p in unique:
                params = {"dir": p}

                if self.config.data["AUTOSCAN_AUTH_ENABLED"]:
                    response = requests.post(
                        self.config.data["AUTOSCAN_ENDPOINT"],
                        params=params,
                        auth=(
                            self.config.data["AUTOSCAN_USERNAME"],
                            self.config.data["AUTOSCAN_PASSWORD"],
                        ),
                    )
                else:
                    response = requests.post(
                        self.config.data["AUTOSCAN_ENDPOINT"], params=params
                    )

                if response.status_code == 200:
                    self._logger.debug(f"Plex scan request: {p}")
                else:
                    self._logger.error(
                        f"Failed to send Plex scan notification: {p}"
                    )
            self._logger.info(f"Processed {len(paths)} scan request(s)")
