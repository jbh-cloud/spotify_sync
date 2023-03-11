import sys
from typing import List

# local imports
from spotify_sync.dataclasses import ProcessedSong
from spotify_sync.deemix_ import DownloadStatus, DeemixDownloader
from spotify_sync.io_ import PersistentDataService
from spotify_sync.config import Config
from spotify_sync.deemix_ import DeemixHelper
from spotify_sync.pushover_ import PushoverClient


class DownloadService:
    def __init__(
        self,
        app_config: Config,
        pd_svc: PersistentDataService,
        pushover: PushoverClient,
    ):
        from spotify_sync.log import get_logger

        self._logger = get_logger().getChild("DownloadService")
        self._pushover = pushover
        self.config = app_config
        self.pd_svc = pd_svc
        self.downloaded_song_paths = []

    def preflight(self) -> None:
        helper = DeemixHelper(self.config)
        if not helper.arl_valid():
            self._pushover.send_message("Failed to validate arl")
            sys.exit(1)

        helper.check_deemix_config()

    def get_songs_to_download(self) -> List[ProcessedSong]:
        processed = self.pd_svc.load_processed_songs()
        
        playlists = {}
        for k, song in processed.items():
            if song.match_pending_download and not song.download_failed:
                self._logger.debug(f"{k} is matched and awaiting download")
                playlist = song.spotify_user_album_id
                if playlist not in playlists:
                    playlists[playlist] = []
                playlists[playlist].append(song)
        return playlists

    def persist_download_status(self, download_statuses) -> None:
        processed = self.pd_svc.load_processed_songs()

        for status in download_statuses:
            if status.success:
                processed[status.spotify_id].match_pending_download = False
                processed[status.spotify_id].downloaded = True
                processed[
                    status.spotify_id
                ].download_isrc = status.downloaded_isrc
                processed[
                    status.spotify_id
                ].download_url = status.downloaded_url
                processed[
                    status.spotify_id
                ].download_path = status.download_path
                processed[status.spotify_id].download_md5 = status.md5
                processed[
                    status.spotify_id
                ].download_bitrate = status.downloaded_bitrate
                processed[status.spotify_id].download_failed = False
                processed[status.spotify_id].download_failed_reason = None
            else:
                processed[status.spotify_id].match_pending_download = True
                processed[status.spotify_id].downloaded = False
                processed[
                    status.spotify_id
                ].download_isrc = status.downloaded_isrc
                processed[
                    status.spotify_id
                ].download_url = status.downloaded_url
                processed[
                    status.spotify_id
                ].download_path = status.download_path
                processed[status.spotify_id].download_md5 = status.md5
                processed[status.spotify_id].download_failed = True
                processed[
                    status.spotify_id
                ].download_failed_reason = "\n".join(
                    [v["message"] for v in status.errors]
                )

        self.pd_svc.persist_processed_songs(processed)

    def get_failed_download_stats(self) -> List[dict]:
        ret = []
        for k, song in self.pd_svc.load_processed_songs().items():
            if song.download_failed:
                ret.append(
                    {
                        "spotifyId": song.spotify_id,
                        "deezerId": song.deezer_id,
                        "title": song.deezer_title,
                        "artist": song.deezer_artist,
                        "error": song.download_failed_reason,
                    }
                )

        return ret

    def get_file_download_paths(self, download_report: List[DownloadStatus]):
        for status in download_report:
            if status.success:
                self.downloaded_song_paths.append(status.download_path)

    def download_missing_tracks(self) -> None:
        songs = self.get_songs_to_download()
        if not songs:
            return
        static_path = self.config.data['DEEMIX_DOWNLOAD_PATH']
        for playlist_name, playlist_songs in songs.items():
            self._logger.info(f"Downloading {len(playlist_songs)} song(s) from Deezer from playlist:"+ playlist_songs[0].spotify_user_album_name)
        # if len(spotify_user_album_id))<1:
            self.config.data['DEEMIX_DOWNLOAD_PATH'] = static_path + "/" \
                +playlist_songs[0].spotify_user_album_name +"  ("+ playlist_name[:4] + ")"
            downloader = DeemixDownloader(
                app_config=self.config, pushover=self._pushover
            )
            downloader.download_songs(playlist_songs)
            failed_songs, succeeded_songs, reports = downloader.get_report()
            self._logger.info(
                f"Successfully downloaded {succeeded_songs}/{len(songs)}"
            )

            self.persist_download_status(reports)
            self.get_file_download_paths(reports)
        self.config.data['DEEMIX_DOWNLOAD_PATH'] = static_path
