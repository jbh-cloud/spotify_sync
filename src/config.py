import json
import os


def load():
    dir = os.path.dirname(__file__)

    with open(os.path.join(dir, '..', 'config.json'), mode='r', encoding='utf-8') as f:
        return json.load(f)
