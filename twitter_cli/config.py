from os import makedirs
from os.path import join, exists, expanduser
import configparser
import json

_root = expanduser('~/.config/twitter-cli')
exists(_root) or makedirs(_root)

_config = None

CONFIG_FILE = join(_root, 'config')
DATABASE_FILE = join(_root, 'data.sqlite3')

_SECTION_PROXY = 'PROXY'
_SECTION_KEYS = 'KEYS'
_SECTION_STORAGE = 'STORAGE'
_SECTION_USERS = 'USERS'

def _load_config():
    global _config

    if _config is None:
        _config = configparser.ConfigParser()

        if exists(CONFIG_FILE):
            _config.read(CONFIG_FILE)
        else:
            _config.add_section(_SECTION_PROXY)
            _config.set(_SECTION_PROXY, 'http', '')
            _config.set(_SECTION_PROXY, 'https', '')

            _config.add_section(_SECTION_KEYS)
            _config.set(_SECTION_KEYS, 'consumer_key', '')
            _config.set(_SECTION_KEYS, 'consumer_secret', '')
            _config.set(_SECTION_KEYS, 'access_token_key', '')
            _config.set(_SECTION_KEYS, 'access_token_secret', '')

            _config.add_section(_SECTION_STORAGE)
            _config.set(_SECTION_STORAGE, 'root_path', '~/Downloads/twitter-cli')
            _config.set(_SECTION_STORAGE, 'timeline', 'timeline')
            _config.set(_SECTION_STORAGE, 'favorite', 'favorite')

            _config.add_section(_SECTION_USERS)
            _config.set(_SECTION_USERS, 'names', '["me", ]')

            with open(CONFIG_FILE, 'wb') as f:
                _config.write(f)

    return _config

def pretty_json_string(dic):
    return json.dumps(dic, sort_keys=True, indent=4)

def get_raw_config():
    output = ''
    config = _load_config()

    for section in config.sections():
        output += '%s: \n' % section
        output += pretty_json_string(dict(config.items(section)))
        output += '\n\n'

    output += 'PATH: %s' % CONFIG_FILE

    return output

def get_proxy():
    return dict(_load_config().items(_SECTION_PROXY))

def get_keys():
    return dict(_load_config().items(_SECTION_KEYS))

def _get_storage_path(is_favorite=False, timeline=None):
    config = _load_config()
    path = config.get(_SECTION_STORAGE, 'root_path')

    if is_favorite:
        path = join(path, config.get(_SECTION_STORAGE, 'favorite'))
    elif timeline:
        path = join(path, config.get(_SECTION_STORAGE, 'timeline'), timeline)

    return expanduser(path)

def get_video_storage_path(is_favorite=False, timeline=None):
    path = join(_get_storage_path(is_favorite, timeline), 'videos')
    exists(path) or makedirs(path)
    return path

def get_photo_storage_path(is_favorite=False, timeline=None):
    path = join(_get_storage_path(is_favorite, timeline), 'photos')
    exists(path) or makedirs(path)
    return path

def get_pinned_users():
    return json.loads(_load_config().get(_SECTION_USERS, 'names'))
