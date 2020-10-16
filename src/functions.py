import spotipy
import json
from spotipy.oauth2 import SpotifyOAuth

def returnSpotifyMethod():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(username='jamesbairdhutchinson',
                                                   scope='user-library-read',
                                                   client_id='33bbbfe2ba9a486ebd39ff4db06c689d',
                                                   client_secret='04c970d3e90f499aac43300552a8326a',
                                                   redirect_uri='http://127.0.0.1:9090'))
    return sp

def pushoverNotification(title,message):
    client = pushoverclient("uafh7b1od8nionuhqqw9u5cjfrxcv3", api_token="a6qu7wdviueeyw328jjzfvmmh5j4sz")
    client.send_message(message, title=title)

