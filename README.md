# spotify_sync
![](run_example.gif)

## Table of contents
* [Introduction](#Introduction)
* [Requirements](#Requirements)
* [Installation](#Installation)
* [Usage](#Usage)
* [Configuration](#Configuration)

## Introduction
This project was written to allow me to synchronise copies of my Spotify songs offline. It also has the bonus of downloading (if available) in lossless quality.

The script caches a copy of all Spotify song metadata, then attempts to match these songs to a Deezer equivalent. Once the batch of songs has been matched it will attempt to download them from Deezer utilising the Deemix Python API.
	
## Requirements
1. Python 3.8 or higher (```sudo apt install python3.8 python-pip```)
2. requirements.txt modules (see below)
3. Spotify account 
4. Deezer account (Free account allows 128kbps downloads, up to lossless requires Deezer Hi-Fi account)
	
## Installation
1. ```python3 -m pip install --upgrade pip```
2. ```pip3 install virtualenv```
3. ```git clone https://github.com/jbh-cloud/spotify_sync.git```
4. ```cd spotify_sync```
5. ```python3 -m venv venv```
6. ```source venv/bin/activate```
7. ```pip install -r requirements.txt```
8. ```cp config.json.example config.json```
9. Configure ```config.json``` as per [Configuration](#Configuration)
10. Run with ```python3 main.py```

## Usage

Simple usage would be..

Cache Spotify OAuth token
```
python main.py -authorize-spotify
```
Run script in automatic mode
```
python main.py -auto
```

Other modes..

```
usage: main.py [-h] (-auto | -authorize-spotify | -sync-liked | -match-liked | -download-missing | -manual-scan | -validate-downloaded-files | -playlist-stats) [--paths [PATHS [PATHS ...]]] [--sync-liked-custom-user]
               [--spotify-client-id SPOTIFY_CLIENT_ID] [--spotify-client-secret SPOTIFY_CLIENT_SECRET] [--spotify-username SPOTIFY_USERNAME] [--liked-songs-path LIKED_SONGS_PATH]

Spotify downloader V1

optional arguments:
  -h, --help            show this help message and exit
  -auto                 Runs the downloader in automatic mode
  -authorize-spotify    Populate OAuth cached creds
  -sync-liked           Queries Spotify for liked songs and downloads metadata
  -match-liked          Queries locally saved liked song metadata and attempts to match on Deezer
  -download-missing     Attempts to download missing songs
  -manual-scan          Invokes Autoscan API against provided paths
  -validate-downloaded-files
                        Enumerates processed songs that are marked as downloaded and validates they are there
  -playlist-stats       Displays stats associated with Spotify playlists
  --paths [PATHS [PATHS ...]]
                        List of paths to scan
  --sync-liked-custom-user
                        Specifies a custom user to query Spotify for
  --spotify-client-id SPOTIFY_CLIENT_ID
                        Custom Spotify user client id
  --spotify-client-secret SPOTIFY_CLIENT_SECRET
                        Custom Spotify user client secret
  --spotify-username SPOTIFY_USERNAME
                        Custom Spotify username
  --liked-songs-path LIKED_SONGS_PATH
                        Path to non-existent json file

```

## Scheduling
Assuming the app has been Spotify authorized at least once, you can run it on a schedule. For example:

Cron (Every day at 2pm)
```
0 14 * * * {FULL_QUAL_PATH_TO_REPO}/venv/bin/python {FULL_QUAL_PATH_TO_REPO}/main.py -auto 
```

## Configuration
All configuration of this tool is done in ```config.json``` an example of which is contained in the project, ```config.json.example```.

### threads

Number of threads to utilise. If not specified, use all available threads.

### deemix

A free Deezer account is required, I would suggest creating a burner account. 

`arl` *required* - [Cookie](https://pastebin.com/Wn7TaZFB) required for Deemix functionality

`download_path` *required* - Path that Deemix will download into

`max_bitrate` *required* - The highest download quality to attempt. Must be one of 'lossless', '320', '128'. 'Lossless' & '320' require a Deezer Hi-Fi account.

`skip_low_quality` *required* - If true and max_bitrate > '128', checks that the Deezer account has privileges to stream the relevant quality. If not it will fail fast (saving you from downloading low quality music). This is especially useful if you rotate Deezer Hi-Fi free trials and don't want to accidentally download 128kbps once your trial has ended.

`strict_matching` *required* If true, it will ONLY successfully match a Spotify song to Deezer via it's ISRC. Setting to false allows fallback to Title - Artist - Album search.

### logging

`level` - *required* - Either 'INFO' or 'DEBUG'

`path` - Path to a non-existent log file, if left blank logs are stored in /logs

### spotify

You will need to create an application as per this [article](https://developer.spotify.com/documentation/general/guides/app-settings/). Ensure you have set the redirect uri to `http://127.0.0.1:{redirect_uri_port}`

`client_id` *required* - Application ID you have setup

`client_secret` *required* - Application secret you have setup

`username` *required* -  Spotify username *must be lower case*

`scope` *required* -  'user-library-read' or 'user-library-read, playlist-read-private' if wanting to download playlists

`redirect_uri_port` *required* - Any usable host port, must match what application has been setup with

#### playlists

`enabled` *required* - Enables / disables inclusion of spotify playlist songs in download

`excluded` *required* - An array of playlists you wish to be excluded from download (case sensitive). You can get the names by running ```python3 main.py -playlist-stats```  

### pushover

`enabled` *required* Enables [Pushover](https://pushover.net/) notifications for script

`user_key` - Pushover user key 

`api_token` - Pushover token (per Pushover application)

### autoscan

`enabled` *required* - Enables [autoscan](https://github.com/Cloudbox/autoscan) integration. Assumes you have set this up correctly and created rewrite rules if needed.

`endpoint` - API endpoint to POST to, usually in the form of IP_ADDR:3030/triggers/manual

`auth_enabled` - If enabled will attempt basic auth

`username` - Autoscan user

`password` - Autoscan password

### git

`enabled` *required* - Enables auto commit of persistent_data_root assuming it is a Git repository..

### data

`persistent_data_root` *required* - Path to local folder used to contain below state files 

#### files

`liked_songs` *required* - Path to existent or non-existent json file. This will store Spotify liked song metadata

`processed_songs` *required* - Path to existent or non-existent json file. This is what the script uses as persistent storage.

`playlist_mapping` *required if [spotify][playlists] is enabled* - Path to existent or non-existent json file. This is where the mapping of songs to playlists is stored.
