import pytest
import unittest

from spotify_sync.dataclasses import Config
from spotify_sync.notification import NotificationType, NotificationClient, PushoverClient


class TestNotificationClient(NotificationClient):
    def _setup(self):
        self._is_enabled = True
        self._is_valid = True

    def send_message(self, message, msg_type: NotificationType) -> None:
        pass


# Tests

class TestNotificationStrategy(unittest.TestCase):
    # unittest.TestCase and pytest fixtures don't play nice, https://github.com/pytest-dev/pytest-mock/issues/174
    @pytest.fixture(autouse=True)
    def __inject_fixtures(self, mocker):
        self.mocker = mocker

    def test_should_send_info(self):
        client = TestNotificationClient(Config(None, 'test', {'NOTIFICATION_STRATEGY': 1}))

        self.assertTrue(client._should_send(NotificationType.INFO))
        self.assertTrue(client._should_send(NotificationType.CHANGE))
        self.assertTrue(client._should_send(NotificationType.FAILURE))

    def test_should_send_change(self):
        client = TestNotificationClient(Config(None, 'test', {'NOTIFICATION_STRATEGY': 2}))

        self.assertFalse(client._should_send(NotificationType.INFO))
        self.assertTrue(client._should_send(NotificationType.CHANGE))
        self.assertTrue(client._should_send(NotificationType.FAILURE))

    def test_should_send_failure(self):
        client = TestNotificationClient(Config(None, 'test', {'NOTIFICATION_STRATEGY': 3}))

        self.assertFalse(client._should_send(NotificationType.INFO))
        self.assertFalse(client._should_send(NotificationType.CHANGE))
        self.assertTrue(client._should_send(NotificationType.FAILURE))

    def test_send_info(self):
        client = TestNotificationClient(Config(None, 'test', {'NOTIFICATION_STRATEGY': 1}))
        self.mocker.patch.object(client, "send_message", return_value=unittest.mock.MagicMock())

        client.send_info('test message')
        client.send_message.assert_called_once()
        client.send_message.assert_called_with('test message', NotificationType.INFO)

    def test_send_change(self):
        client = TestNotificationClient(Config(None, 'test', {'NOTIFICATION_STRATEGY': 1}))
        self.mocker.patch.object(client, "send_message", return_value=unittest.mock.MagicMock())

        client.send_change('test message')
        client.send_message.assert_called_once()
        client.send_message.assert_called_with('test message', NotificationType.CHANGE)

    def test_send_failure(self):
        client = TestNotificationClient(Config(None, 'test', {'NOTIFICATION_STRATEGY': 1}))
        self.mocker.patch.object(client, "send_message", return_value=unittest.mock.MagicMock())

        client.send_failure('test message')
        client.send_message.assert_called_once()
        client.send_message.assert_called_with('test message', NotificationType.FAILURE)


@pytest.fixture()
def pushover_client_user():
    class PushoverClientUser:
        def __init__(self):
            self.is_authenticated = True

        def send_message(self):
            pass

    return PushoverClientUser()


@pytest.fixture()
def pushover_client_app():
    class PushoverClientApp:
        def __init__(self):
            self.is_authenticated = True

    return PushoverClientApp()


@pytest.fixture
def pushover_config():
    return Config(None, 'test', {
        'NOTIFICATION_STRATEGY': 1,
        'NOTIFICATION_PROVIDER_PUSHOVER_ENABLED': True,
        'NOTIFICATION_PROVIDER_PUSHOVER_API_TOKEN': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        'NOTIFICATION_PROVIDER_PUSHOVER_USER_KEY': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    })


@pytest.fixture
def pushover_client(mocker, pushover_config):
    client = PushoverClient(pushover_config)

    mocker.patch.object(client, "_is_valid", return_value=True)
    mocker.patch.object(client, "_get_title", return_value="Test title")

    mock_user = mocker.patch.object(client, "_user", create=True)
    mock_user.return_value.send_message.return_value = unittest.mock.MagicMock()

    return client


class TestPushoverClient:
    def test_api_is_called_if_valid(self, pushover_client):
        pushover_client.send_message("test", NotificationType.INFO)

        pushover_client._user.send_message.assert_called_once()
