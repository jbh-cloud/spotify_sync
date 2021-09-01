from git import Repo

# Local imports
from src import config
from src.log import rootLogger
from src import pushover_api

logger = rootLogger.getChild('GIT_API')
config = config.load()


def assert_repo():
    if config['git']['enabled']:
        try:
            assert check_repo_is_clean()
        except:
            logger.error(f'Git repo specified is not clean')
            pushover_api.send_notification('Spotify downloader', 'Git repo specified is not clean')
            raise Exception(f'Git repo specified is not clean')


def check_repo_is_clean():
    logger.debug(f'Checking {config["git"]["persistent_data_folder_path"]} is clean')
    repo = Repo(config['git']['persistent_data_folder_path'])
    return not repo.is_dirty() and len(repo.untracked_files) == 0


def commit_files(message):
    if config['git']['enabled']:
        repo = Repo(config['git']['persistent_data_folder_path'])
        if repo.is_dirty() or len(repo.untracked_files) != 0:
            logger.debug(f'Commiting files in {config["git"]["persistent_data_folder_path"]}')
            repo.git.add(all=True)
            repo.git.commit(
                '-m',
                message,
                author='spotify_downloader <automation@jbh.cloud>')




