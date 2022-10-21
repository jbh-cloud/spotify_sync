from chump import Application

# local imports
from spotify_sync.config import Config


class PushoverClient:
    def __init__(self, app_config: Config = None):
        from spotify_sync.log import get_logger

        self.config = app_config
        self._logger = get_logger().getChild("PushoverClient")
        self._app = None
        self._user = None
        self.valid = False
        self.enabled = False
        self.initialize()

    def _validate(self):
        if not self._user.is_authenticated or not self._app.is_authenticated:
            self._logger.warning(
                "Failed to validate Pushover connection details"
            )
        else:
            self.valid = True

    def _get_title(self):
        return (
            f'spotify_sync - {self.config.data["SPOTIFY_USERNAME"]}'
            if self.config.profile is None
            else f"spotify_sync - profile: {self.config.profile}"
        )

    def initialize(self):
        if self.config is not None and self.config.data["PUSHOVER_ENABLED"]:
            self.enabled = True
            self._app = Application(self.config.data["PUSHOVER_API_TOKEN"])
            self._user = self._app.get_user(
                self.config.data["PUSHOVER_USER_KEY"]
            )
            self._validate()

    def send_message(self, message: str):
        if self.enabled:
            if self.valid:
                self._user.send_message(
                    title=self._get_title(), message=message
                )
            else:
                self._logger.warning(
                    f"Pushover details are invalid, unable to send: {message}"
                )
