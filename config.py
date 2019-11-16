from os import mkdir, pathsep
from os.path import join, exists, expanduser
import configparser
import json

_root = expanduser('~/.twitter-cli')
exists(_root) or mkdir(_root)

_config = None
_config_file = join(_root, 'config')

DATABASE_FILE = join(_root, 'data.sqlite3')

_SECTION_PROXY = 'PROXY'
_SECTION_KEYS = 'KEYS'
_SECTION_STORAGE = 'STORAGE'

def _load_config():
    global _config

    if _config is None:
        config = configparser.ConfigParser()

        if exists(_config_file):
            config.read(_config_file)
        else:
            config.add_section(_SECTION_PROXY)
            config.set(_SECTION_PROXY, 'http', '')
            config.set(_SECTION_PROXY, 'https', '')

            config.add_section(_SECTION_KEYS)
            config.set(_SECTION_KEYS, 'consumer_key', '')
            config.set(_SECTION_KEYS, 'consumer_secret', '')
            config.set(_SECTION_KEYS, 'access_token_key', '')
            config.set(_SECTION_KEYS, 'access_token_secret', '')

            config.add_section(_SECTION_STORAGE)
            config.set(_SECTION_STORAGE, 'videos', '')
            config.set(_SECTION_STORAGE, 'pictures', '')

            with open(_config_file, 'wb') as f:
                config.write(f)

    return config

def get_proxy():
    return dict(_load_config().items(_SECTION_PROXY))

def get_keys():
    return dict(_load_config().items(_SECTION_KEYS))

def get_video_storage_path():
    path = _load_config().get(_SECTION_STORAGE, 'videos')
    path = path if path else '~' + pathsep + 'Downloads'

    return expanduser(path)

def get_picture_storage_path():
    path = _load_config().get(_SECTION_STORAGE, 'pictures')
    path = path if path else '~' + pathsep + 'Downloads'

    return expanduser(path)
