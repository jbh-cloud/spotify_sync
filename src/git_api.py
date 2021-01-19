from git import Repo
import src.config as config
from src.download import return_download_commence

config = config.load()


def check_repo_is_clean():
    repo = Repo(config['git']['data_folder_path'])
    return not repo.is_dirty() and len(repo.untracked_files) == 0


def commit_files():
    if config['git']['auto_commit_persistent_data_folder']:
        repo = Repo(config['git']['data_folder_path'])
        if repo.is_dirty() or len(repo.untracked_files) != 0:
            repo.git.add(all=True)
            repo.git.commit('-m', f'Spotify Downloader auto commit {return_download_commence()}', author='spotify_downloader <automation@jbh.cloud>')


#def push_commit():
#    if config['git']['auto_commit_persistent_data_folder']:
#        try:
#            repo = Repo(config['git']['data_folder_path'])
#            #origin = repo.remote(name='origin')
#            with repo.git.custom_environment(GIT_SSH_COMMAND=f'ssh -v -i {config["git"]["ssh_key_path"]} -oIdentitiesOnly=yes -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null "$@"'):
#                repo.remotes.origin.push()
#            #origin.push()
#        except:
#            print('Some error occured while pushing the code')


if config['git']['auto_commit_persistent_data_folder']:
    try:
        assert check_repo_is_clean()
    except:
        raise Exception(f'Git repo specified is not clean')


push_commit()