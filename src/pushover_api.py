from pushover import Client

# local imports
from src import config

config = config.load()

if config['pushover']['enabled']:
    client = Client(config['pushover']['user_key'], api_token=config['pushover']['api_token'])


def send_notification(title, message):
    if config['pushover']['enabled']:
        client.send_message(message, title=title)

