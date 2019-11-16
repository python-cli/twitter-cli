import requests
from urlparse import urlparse
from os.path import join, split, exists
from config import *

def _download(url, output_dir, extension):
    try:
        paths = split(urlparse(url).path)
        filepath = join(output_dir, paths[-1])

        if '.' not in filepath:
            filepath = '%s.%s' % (filepath, extension)

        if exists(filepath):
            print('Found existing file here, reusing it...')
            return filepath

        response = requests.get(url, proxies=get_proxy())
        print('Downloaded to %s' % filepath)

        with open(filepath, 'wb') as f:
            f.write(response.content)
    except:
        filepath = None

    return filepath

def download_video(url, extension='mp4'):
    return _download(url, get_video_storage_path(), extension)

def download_photo(url, extension='jpg'):
    return _download(url, get_photo_storage_path(), extension)
