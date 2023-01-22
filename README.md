# spotify_sync
[![Python Versions](https://img.shields.io/pypi/pyversions/spot_sync)](https://pypi.org/project/spotify-sync/)
[![PyPi package](https://img.shields.io/pypi/v/spot-sync)](https://pypi.org/project/spot-sync/)
[![Downloads](https://static.pepy.tech/badge/spot-sync/month)](https://pepy.tech/project/spot-sync)
[![License](https://img.shields.io/github/license/jbh-cloud/spotify_sync)](https://github.com/jbh-cloud/spotify_sync/blob/main/LICENSE.md)
[![Documentation](https://img.shields.io/badge/docs-%20-yellow)](https://docs.spotify-sync.jbh.cloud/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)]()

![](run_example.gif)

## Introduction

spotify_sync is a CLI app written in Python allowing you to download songs from your Spotify account. It is designed to be a 'set and forget' tool for users wanting to keep an offline copy of their library. Spotify songs are matched to a 1:1 Deezer equivalent via their [ISRC](https://en.wikipedia.org/wiki/International_Standard_Recording_Code) and then queued for download.

#### Features:

* Download of liked songs
* Download of playlist songs
* Up-to lossless quality downloads
* Multi-threaded downloading
* Scheduling (e.g. cron)
* Multi-config support; configure and schedule multiple profiles with separate Spotify accounts
* Backup and restore of config and persistent data
* Notification support via [Pushover](https://pushover.net/)
* Automatic Plex library scanning via [Autoscan](https://github.com/Cloudbox/autoscan)


## Requirements
1. Python & pip >= 3.8
2. Spotify account (Free)
3. Deezer account (Free allows 128kbps downloads, up to lossless requires Deezer Hi-Fi account)


## Install

```
python3 -m pip install -U spot_sync
```

## Usage

*Simple usage would be..*

Cache Spotify OAuth token
```
spotify_sync utils authorize-spotify --profile myFirstProfile
```

Run in automatic mode
```
spotify_sync run auto --profile myFirstProfile
```

## Documentation

Further configuration is required, details for which can be found at the [docs](https://docs.spotify-sync.jbh.cloud/).


## Support

If you use or enjoy this project, please give it a :star: or

<a href="https://www.buymeacoffee.com/jbhcloud" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>


### Disclaimer

This tool was written for educational purposes. I will not be responsible if you use this program in bad faith. By using it, you are accepting the [Deezer Terms of Use](https://www.deezer.com/legal/cgu).
    spotify_sync is not affiliated with Deezer.
