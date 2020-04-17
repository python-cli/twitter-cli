
import logging
import requests
from urlparse import urlparse
from os.path import join, split, exists
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import *

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor()

def _download(url, output_dir, prefix, extension):
    try:
        paths = split(urlparse(url).path)
        filename = paths[-1]

        if '.' in filename:
            filename = '%s-%s' % (prefix, filename)
        else:
            filename = '%s-%s.%s' % (prefix, filename, extension)

        filepath = join(output_dir, filename)

        if exists(filepath):
            logger.info('Found existing file here, reusing it...')
            return filepath

        def task(url):
            logger.info('Downloading %s' % url)
            response = requests.get(url, proxies=get_proxy())
            logger.info('Downloaded to %s' % filepath)

            with open(filepath, 'wb') as f:
                f.write(response.content)

        executor.submit(task, (url))
    except requests.RequestException as e:
        logger.exception(e)
        filepath = None

    return filepath

def download_video(url, output_dir, prefix='', extension='mp4'):
    return _download(url, output_dir, prefix, extension)

def download_photo(url, output_dir, prefix='', extension='jpg'):
    return _download(url, output_dir, prefix, extension)

def wait_for_download_completed():
    executor.shutdown()
