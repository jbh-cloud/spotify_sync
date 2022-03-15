import os


def ensure_directory(path: str):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        try:
            os.makedirs(dir)
        except Exception as e:
            raise Exception(f'Failed to ensure that directory exists. path="{path}"') from e