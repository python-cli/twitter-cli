import logging
import requests

from .config import get_bark_key

logger = logging.getLogger(__name__)

def send_notification(title, message=None):
    key = get_bark_key()

    if not (key and len(key) > 0):
        logger.warning('Empty key configuration for Bark!')
        return False

    url = 'https://api.day.app/%s' % key

    if title:
        url += '/%s' % title

    if message:
        url += '/%s' % message

    r = requests.get(url)

    if r.status_code != requests.codes.ok:
        logger.error('Failed to send request with error: %s' % r.text)
        return

    json_data = r.json()

    if json_data.get('code', 0) != 200:
        logger.error(json_data.get('message'))
        return False

    return True
