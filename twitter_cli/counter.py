
import logging
from datetime import datetime
from .notification import *

logger = logging.getLogger(__name__)

class Counter(object):
    _success = 0
    _failure = 0
    _reset_func = None
    _reset_time = datetime.now()

    @classmethod
    def success(cls, count=1):
        cls._success += count
        cls._try_reset()

    @classmethod
    def failure(cls, count=1):
        cls._failure += count
        cls._try_reset()

    @classmethod
    def set_reset_handler(cls, func):
        cls._reset_func = func

    @classmethod
    def _try_reset(cls):
        reset_func = cls._reset_func

        if reset_func and callable(reset_func):
            if reset_func(cls._success, cls._failure, cls._reset_time):
                print 'resetting'
                cls._success = 0
                cls._failure = 0
                cls._reset_time = datetime.now()

# ---------------------------------------------

@staticmethod
def handler(success, failure, time):
    if (datetime.now() - time).days >= 1:
        title = '[twitter-cli] Found %d new tweet(s)' % (success + failure)
        message = 'Including %d success and %d failure.' % (success, failure)
        send_notification(title, message)
        return True

    return False

Counter.set_reset_handler(handler)
