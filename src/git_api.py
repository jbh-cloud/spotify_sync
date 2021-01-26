from git import Repo
import src.config as config
from src.download import return_download_commence
from src.log import rootLogger

logger = rootLogger.getChild('GIT_API')

config = config.load()


def assert_repo():
    if config['git']['enabled']:
        try:
            assert check_repo_is_clean()
        except:
            logger.error(f'Git repo specified is not clean')
            raise Exception(f'Git repo specified is not clean')


def check_repo_is_clean():
    logger.debug(f'Checking {config["git"]["persistent_data_folder_path"]} is clean')
    repo = Repo(config['git']['persistent_data_folder_path'])
    return not repo.is_dirty() and len(repo.untracked_files) == 0


def commit_files():
    if config['git']['enabled']:
        repo = Repo(config['git']['persistent_data_folder_path'])
        if repo.is_dirty() or len(repo.untracked_files) != 0:
            logger.debug(f'Commiting files in {config["git"]["persistent_data_folder_path"]}')
            repo.git.add(all=True)
            repo.git.commit('-m', f'Spotify Downloader auto commit {return_download_commence()}', author='spotify_downloader <automation@jbh.cloud>')




