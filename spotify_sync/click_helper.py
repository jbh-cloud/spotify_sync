from click import argument, option, Option, UsageError, Path, STRING, Choice, BOOL
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

# local imports
from spotify_sync.config import set_env


def notify_config(ctx, param, value):
    if param.name == "config":
        set_env(value, "MANUAL_CONFIG_FILE")

    if param.name == "profile":
        set_env(value, "CONFIG_PROFILE")

    if param.name == "verbose" and value is True:
        set_env("DEBUG", "LOG_LEVEL")


config_option_group = optgroup.group(
    "Input config object",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="The sources of the config input",
)
config_option_file = optgroup.option(
    "--config",
    type=Path(exists=True),
    callback=notify_config,
    help="Path to a separate config file",
)
config_option_profile = optgroup.option(
    "--profile",
    type=STRING,
    callback=notify_config,
    help="Path to a separate config file",
)

backup_output_dir = option(
    "--out-dir",
    "-o",
    required=False,
    type=Path(exists=True, dir_okay=True, file_okay=False),
    help="Output folder to backup to",
)

restore_zip_file = argument("zip_file", type=Path(exists=True), required=True)

restore_zip_file_profile = option(
    "--new-profile", type=STRING, required=False, help="New profile name to restore to"
)

restore_zip_file_force_overwrite = option(
    "-f",
    "--force",
    default=False,
    is_flag=True,
    required=True,
    help="Overwrites destination profile or persistent files if they exist",
)

spotify_songs_path = option(
    "--spotify",
    required=True,
    type=Path(exists=True),
    help="Path to a Spotify song json file to migrate",
)

processed_songs_path = option(
    "--processed",
    required=True,
    type=Path(exists=True),
    help="Path to a processed song json file to migrate",
)

migrated_profile_name = option(
    "--profile",
    required=True,
    type=STRING,
    help="Name of a (non existent) profile to migrate settings to",
)

migrated_config_schema_mode = option(
    "--config-schema-mode",
    type=Choice(["legacy", "latest"], case_sensitive=False),
    show_default=True,
    default="legacy",
    help="Specify schema of config file",
)

config_list_detailed = option(
    "--detailed",
    "-d",
    required=False,
    is_flag=True,
    help="Display additional information",
)

log_level = option(
    "--verbose",
    "-v",
    required=False,
    is_flag=True,
    callback=notify_config,
    help="Sets verbosity to DEBUG",
)
