# spotify_download

## Table of contents
* [Introduction](#Introduction)
* [Requirements](#Requirements)
* [Installation](#Installation)
* [Usage](#Usage)
* [Configuration](#Configuration)

## Introduction
This project was written to allow me to save my Spotify tracks in flac and a safe location to safe guard from Spotify licensing deals expiring. In its current iteration it is setup to download 'liked' tracks.
	
## Requirements
1. Ubuntu/Debian/Windows
2. Python 3.6 or higher (```sudo apt install python3.8 python-pip```)
3. requirements.txt modules (see below)
	
## Installation
1. ```git clone https://github.com/jbh-cloud/spotify_download.git```
2. ```cd spotify_download```
3. ```sudo python3 -m pip install -r requirements.txt```
4. ```cp config.json.example config.json```
5. Configure ```config.json``` as per [Configuration](#Configuration)
6. Run with ```python3 main.py```

## Usage

Simple usage would be..

Cache Spotify OAuth token
```
main.py --authorize-spotify
```
Run script in automatic mode
```
main.py --auto
```

Other modes..

```
usage: main.py [-h]
		(--auto | --authorize-spotify | --sync-liked | --match-liked | --download-missing)
		[--sync-liked-custom-user]
		[--spotify-client-id SPOTIFY_CLIENT_ID]
		[--spotify-client-secret SPOTIFY_CLIENT_SECRET]
		[--spotify-username SPOTIFY_USERNAME]
		[--liked-songs-path LIKED_SONGS_PATH]
```


## Configuration
All configuration of this tool is done in ```config.json``` an example of which is contained in the project, ```config.json.example```.

### deemix

A free Deezer account is required, I would suggest creating a burner account. 

`config_path` *required* - Path to folder that contains deemix config.json. Deemix logs and Deezer cached authenication token will be stored here too.

`arl` *required* - [Cookie](https://pastebin.com/Wn7TaZFB) required for Deemix functionality

`download_path` *required* - Path that Deemix will download into

### logging

`level` - *required* - Either 'INFO' or 'DEBUG'

`path` - Path to a non existent log file, if left blank logs are stored in /logs

### spotify

You will need to create an application as per this [article](https://developer.spotify.com/documentation/general/guides/app-settings/). Ensure you have set the redirect uri to `http://127.0.0.1:{redirect_uri_port}`

`client_id` *required* - Application ID you have setup

`client_secret` *required* - Application secret you have setup

`username` *required* -  Spotify username *must be lower case*

`scope` *required* -  'user-library-read'

`redirect_uri_port` *required* - Any usable host port, must match what application has been setup with

### pushover

`enabled` - Enables pushover notifications for script

`user_key` - Pushover user key 

`api_token` - Pushover token (per Pushover application)

### autoscan

`enabled` - Enables [autoscan](https://github.com/Cloudbox/autoscan) integration. Assumes you have set this up correctly and created rewrite rules if needed.

`endpoint` - API endpoint to POST to, usually in the form of IP_ADDR:3030/triggers/manual

`auth_enabled` - If enabled will attempt basic auth

`username` - Autoscan user

`password` - Autoscan password

### git

`enabled` - Enables auto commit of a local repo.

`persistent_data_folder_path` - I have this set to repo containing `[deemix][config_path]`, `[script][paths][liked_songs]` & `[script][paths][processed_songs]` to ensure persistent data is git.

### script

`[paths][liked_songs]` *required* - Path to existent or non-existent json file. This will store Spotify liked song metadata

`[paths][processed_songs]` *required* - Path to existent or non-existent json file. This is what the script uses as persistent storage. 

`[spotify_playlists][enabled]` - Enables / disables inclusion of spotify playlist songs in download

`[spotify_playlists][excluded]` - An array of playlists you wish to be excluded from download (case sensitive)