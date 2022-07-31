from pathlib import Path
from appdirs import AppDirs

_dirs = AppDirs("spotify_sync", "jbh-cloud")

CONFIG = Path(_dirs.user_config_dir)
DATA = Path(_dirs.user_data_dir)

Path(CONFIG).mkdir(parents=True, exist_ok=True)
Path(DATA).mkdir(parents=True, exist_ok=True)
