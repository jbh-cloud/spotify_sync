# spotify_download

## Table of contents
* [Introduction](#Introduction)
* [Requirements](#Requirements)
* [Installation](#Installation)
* [Configuration](#Configuration)

## Introduction
This project was written to allow me to save my Spotify tracks in flac and a safe location to safe guard from Spotify licensing deals expiring. In its current iteration it is setup to download 'liked' tracks.
	
## Requirements
1. Ubuntu/Debian/Windows
2. Python 3.6 or higher (```sudo apt install python python-pip```)
3. requirements.txt modules (see below)
	
## Installation
1. ```git clone https://github.com/jbh-cloud/spotify_download.git```
2. ```cd spotify_download```
3. ```sudo python3 -m pip install -r requirements.txt```
4. ```cp config.json.example config.json```
5. Configure ```config.json``` as per [Configuration](#Configuration)
6. Run with ```python3 main.py```


## Configuration
All configuration of this tool is done in ```config.json``` an example of which is contained in the project, ```config.json.example```.
