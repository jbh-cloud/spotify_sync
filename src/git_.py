from git import Repo

# Local imports
from src.config import load as load_config
from src.log import rootLogger
from src import pushover_

logger = rootLogger.getChild('GIT')
config = load_config()


def assert_repo():
    if config["GIT_ENABLED"]:
        try:
            assert repo_is_clean()
        except:
            logger.error(f'Git repo specified is not clean')
            pushover_.send_notification('Spotify downloader', 'Git repo specified is not clean')
            raise Exception(f'Git repo specified is not clean')


def repo_is_clean():
    logger.debug(f'Checking {config["DATA_PERSISTENT_DATA_ROOT"]} is clean')
    repo = Repo(config["DATA_PERSISTENT_DATA_ROOT"])
    return not repo.is_dirty() and len(repo.untracked_files) == 0


def commit_files(message):
    if config["GIT_ENABLED"]:
        repo = Repo(config["DATA_PERSISTENT_DATA_ROOT"])
        if repo.is_dirty() or len(repo.untracked_files) != 0:
            logger.debug(f'Commiting files in {config["DATA_PERSISTENT_DATA_ROOT"]}')
            repo.git.add(all=True)
            repo.git.commit(
                '-m',
                message,
                author='spotify_sync <automation@nowhere>')




