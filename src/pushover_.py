from chump import Application

# local imports
from src.config import load as load_config
from src.log import rootLogger

config = load_config()


class PushoverClient:
    def __init__(self, user_key: str, app_token: str):
        self._logger = rootLogger.getChild('PUSHOVER')
        self._app = None
        self._user = None
        self._user_key = user_key
        self._app_token = app_token
        self.valid = True
        self.initialise()

    def _validate(self):
        if not self._user.is_authenticated and self._app.is_authenticated:
            self._logger.warning("Failed to validate Pushover connection details")
            self.valid = False

    def initialise(self):
        self._app = Application(self._app_token)
        self._user = self._app.get_user(self._user_key)
        self._validate()

    def send_message(self, title: str, message: str):
        if self.valid:
            self._user.send_message(title=title, message=message)
        else:
            self._logger.warning(f"Pushover details are invalid, unable to send: {message}")


if config["PUSHOVER_ENABLED"]:
    client = PushoverClient(user_key=config["PUSHOVER_USER_KEY"], app_token=config["PUSHOVER_API_TOKEN"])


def send_notification(title, message):
    if config["PUSHOVER_ENABLED"]:
        client.send_message(title, message)

