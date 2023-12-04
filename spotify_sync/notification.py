import logging
from abc import abstractmethod
from enum import Enum
from chump import Application

from spotify_sync.dataclasses import Config


class NotificationType(Enum):
    INFO = 1
    CHANGE = 2
    FAILURE = 3


class NotificationClient:
    def __init__(self, app_config: Config):
        assert app_config is not None

        self._logger = self._get_logger()
        self._app_config = app_config
        self._strategy = NotificationType(
            self._app_config.data["NOTIFICATION_STRATEGY"]
        )
        self._is_valid = False
        self._is_enabled = False
        self._strategy_map = {
            NotificationType.INFO: (
                NotificationType.INFO,
                NotificationType.CHANGE,
                NotificationType.FAILURE,
            ),
            NotificationType.CHANGE: (
                NotificationType.CHANGE,
                NotificationType.FAILURE,
            ),
        }

    @property
    def is_valid(self) -> bool:
        return self._is_valid

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    @property
    def app_config(self) -> Config:
        return self._app_config

    @abstractmethod
    def send_message(self, message, msg_type: NotificationType) -> None:
        raise NotImplementedError

    def send_info(self, message) -> None:
        self.send_message(message, NotificationType.INFO)

    def send_change(self, message) -> None:
        self.send_message(message, NotificationType.CHANGE)

    def send_failure(self, message) -> None:
        self.send_message(message, NotificationType.FAILURE)

    @abstractmethod
    def _setup(self):
        raise NotImplementedError

    @classmethod
    def _get_logger(cls) -> logging.Logger:
        from spotify_sync.log import get_logger

        return get_logger().getChild(cls.__name__)

    def _get_title(self):
        return (
            f"spotify_sync - {self._app_config.data['SPOTIFY_USERNAME']}"
            if self._app_config.profile is None
            else f"spotify_sync - profile: {self._app_config.profile}"
        )

    def _should_send(self, msg_type: NotificationType) -> bool:
        if self._strategy == msg_type:
            return True

        if (
            self._strategy in self._strategy_map
            and msg_type in self._strategy_map[self._strategy]
        ):
            return True

        return False


class PushoverClient(NotificationClient):
    def __init__(self, app_config: Config):
        super().__init__(app_config)

        self._app = None
        self._user = None
        self._setup()

    def send_message(self, message: str, msg_type: NotificationType):
        if self._is_enabled and self._should_send(msg_type):
            if self._is_valid:
                try:
                    self._user.send_message(
                        title=self._get_title(), message=message
                    )
                except Exception as e:
                    self._logger.warning(
                        f"Failed to send Pushover message, error: {e}"
                    )
            else:
                self._logger.warning(
                    f"Pushover details are invalid, unable to send: {message}"
                )

    def _setup(self):
        if self._app_config.data["NOTIFICATION_PROVIDER_PUSHOVER_ENABLED"]:
            self._is_enabled = True
            self._app = Application(
                self._app_config.data[
                    "NOTIFICATION_PROVIDER_PUSHOVER_API_TOKEN"
                ]
            )
            self._user = self._app.get_user(
                self._app_config.data[
                    "NOTIFICATION_PROVIDER_PUSHOVER_USER_KEY"
                ]
            )
            self._validate()

    def _validate(self):
        if not self._user.is_authenticated or not self._app.is_authenticated:
            self._logger.warning(
                "Failed to validate Pushover connection details"
            )
        else:
            self._is_valid = True
