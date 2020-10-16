from flask import Flask
import requests

app = Flask(__name__)


DEEZER_APP_ID = "439522"
DEEZER_APP_SECRET = "c86f30ebeba56bd702a33182f425cc24"
DEEZER_REDIRECT_URI = "http://127.0.0.1:5000/deezer/login"


@app.route('/', methods=['GET'])
def default():
    url = (f'https://connect.deezer.com/oauth/auth.php?app_id={DEEZER_APP_ID}'
           f'&redirect_uri={DEEZER_REDIRECT_URI}&perms=basic_access,email')
    return redirect(url)


# This path should be your redirect url
@app.route('/deezer/login', methods=['GET'])
def deezer_login():
    # retrieve the authorization code given in the url
    code = requests.args.get('code')

    # request the access token
    url = (f'https://connect.deezer.com/oauth/access_token.php?app_id={DEEZER_APP_ID}'
           f'&secret={DEEZER_APP_SECRET}&code={code}&output=json')
    response = requests.get(url)

    # If it's not a good code we will get this error
    if response.text == 'wrong code':
        return 'wrong code'

    # We have our access token
    response = response.json()
    return response['access_token']

if __name__ == '__main__':
    app.run()