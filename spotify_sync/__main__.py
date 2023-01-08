import typing
import click

# local imports
from spotify_sync.cli import SpotifySyncApp
from spotify_sync.click_helper import (
    restore_zip_file,
    log_level,
    config_option_group,
    config_option_file,
    config_option_profile,
    spotify_songs_path,
    processed_songs_path,
    migrated_profile_name,
    migrated_config_schema_mode,
    restore_zip_file_force_overwrite,
    restore_zip_file_profile,
    backup_output_dir,
    force_spotify_reauth,
)

app = SpotifySyncApp()


@click.group()
def cli() -> None:
    """
    spotify_sync

    A schedulable, configurable CLI downloader for Spotify accounts
    """


@cli.group()
def run() -> None:
    """
    Run spotify_sync in different modes
    """


@run.command("auto")
@log_level
@config_option_group
@config_option_file
@config_option_profile
def auto(config, profile, verbose) -> None:
    """Runs spotify_sync in automatic mode"""
    app.auto()


@run.command("sync-spotify")
@config_option_group
@config_option_file
@config_option_profile
@log_level
def sync_spotify(config, profile, verbose) -> None:
    """Download Spotify song metadata associated with account"""
    app.sync_spotify()


@run.command("match-spotify")
@config_option_group
@config_option_file
@config_option_profile
@log_level
def match_spotify(config, profile, verbose) -> None:
    """Match unprocessed Spotify songs to Deezer equivalents"""
    app.match_spotify()


@run.command("download-missing")
@config_option_group
@config_option_file
@config_option_profile
@log_level
def download_missing(config, profile, verbose) -> None:
    """Downloads matched songs pending download"""
    app.download_missing()


@cli.group()
def utils() -> None:
    """
    Helper commands
    """


@utils.command("authorize-spotify")
@force_spotify_reauth
@config_option_group
@config_option_file
@config_option_profile
@log_level
def authorize_spotify(force_reauth, config, profile, verbose) -> None:
    """Caches Spotify OAuth token"""
    app.authorize_spotify(force_reauth)


@utils.command("migrate-config")
@config_option_group
@config_option_file
def migrate_config(config) -> None:
    """Migrate legacy config file"""
    app.migrate_config()


@utils.command("migrate-to-profile")
@config_option_group
@config_option_file
@spotify_songs_path
@processed_songs_path
@migrated_profile_name
@migrated_config_schema_mode
def migrate_to_profile(
    config, spotify, processed, profile, config_schema_mode
) -> None:
    """Migrate historical config and cache to a profile"""
    legacy = config_schema_mode == "legacy"
    app.migrate_to_profile(spotify, processed, profile, legacy)


@utils.command("manual-scan")
@click.argument("paths", required=True, type=click.STRING, nargs=-1)
def manual_plex_scan(paths: typing.Tuple[str]) -> None:
    """
    Manually invokes Autoscan with provided paths

    E.g. manual-scan /path/to/file/1 /path/to/file/2
    """
    app.scan([p for p in paths])


# @utils.command("validate-downloaded-files")
# @config_option_group
# @config_option_file
# @config_option_profile
# def validate_downloaded_files(config, profile) -> None:
#     """Validates processed songs are still on disk"""
#     app.validate_downloaded_files()


@cli.group()
def backup() -> None:
    """
    Backup config and persistent data
    """


@backup.command("local")
@config_option_group
@config_option_file
@config_option_profile
@backup_output_dir
def backup_local(config, profile, out_dir) -> None:
    """
    Backup to the current working directory
    """
    app.local_backup(out_dir)


@cli.command("restore")
@restore_zip_file
@restore_zip_file_profile
@restore_zip_file_force_overwrite
def restore(zip_file, new_profile, force) -> None:
    """
    Restore an existing backup
    """
    app.local_restore(zip_file, force=force, new_profile=new_profile)


@cli.group()
def stats() -> None:
    """
    Display stats from various sources
    """


@stats.command("playlists")
@config_option_group
@config_option_file
@config_option_profile
def playlist_stats(config, profile) -> None:
    """
    Display playlist stats associated with account
    """
    app.playlist_stats()


@stats.command("failed-download")
@config_option_group
@config_option_file
@config_option_profile
def failed_download_stats(config, profile) -> None:
    """
    Display historical failed song download stats
    """
    app.failed_download_stats()


@cli.group()
def config() -> None:
    """
    Access app configurations
    """


@config.command("add")
@click.argument("name", required=True)
@click.argument("path", required=True, type=click.Path(exists=True))
def config_add(name, path) -> None:
    """
    Add a config profile to the cache
    """
    app.cache_config_profile(name, path)


@config.command("remove")
@click.argument("name", required=True)
def config_remove(name) -> None:
    """
    Remove a config profile from the cache
    """
    app.remove_config_profile(name)


@config.command("list")
def config_list() -> None:
    """
    List cached config profiles
    """
    app.list_config_profiles()


@config.command("list-paths")
def config_list_paths() -> None:
    """
    List cached config profile paths
    """
    app.list_config_profile_paths()


@config.command("generate")
def config_generate() -> None:
    """
    Generate an example config file
    """
    app.generate_example_config()


if __name__ == "__main__":
    cli()
