#!/usr/bin/env python

from logger import getLogger
import twitter
from os.path import split
from time import sleep

from config import *
from models import *
from downloader import *

api = twitter.Api(proxies=get_proxy(), **get_keys())
logger = getLogger(__name__)

def print_sample_entity(prefix, entities):
    if not entities:
        entities = 'Empty'

    if type(entities) in (type, list):
        entity = entities[0] if len(entities) > 0 else ''
        logger.info('\nCount of %s: %d' % (prefix, len(entities) if entities else 0))
    else:
        entity = entities

    if isinstance(entity, twitter.models.TwitterModel):
        content = pretty_json_string(entity.AsDict())
    elif isinstance(entity, dict):
        content = pretty_json_string(entity)
    else:
        content = str(entity)

    logger.info(prefix + content)

def destroy_favorited_status(status):
    if not status or not status.id:
        return False

    try:
        logger.info('Destroying the favorited status %s' % status.id)
        result = api.DestroyFavorite(status=status)
        logger.info('Destroy finished!')
        return result != None
    except twitter.TwitterError as e:
        logger.exception(e)

        if e.args[0][0]['code'] == 144:
            # TwitterError: No status found with that ID
            # Let's just pretend it as suceed.
            return True

    return False

def save_statuses(statuses):
    for status in statuses:
        s = Status.initialize(status)

        logger.debug('Status: %s\n%s:[\n%s\n]' % (s.id, s.user.name, s.text))

        video = s.video

        if video:
            logger.debug('Found video: %s' % video)
            extension = split(video.content_type)[-1]
            filepath = download_video(video.video_url, extension=extension)

            if filepath:
                video.downloaded_path = filepath
                video.save()

                if destroy_favorited_status(status):
                    continue
            else:
                logger.error('Download video failed?')

        if s.is_photo:
            for p in s.photos:
                logger.debug('Found photo: %s' % p)
                filepath = download_photo(p.media_url_https or p.media_url)

                if filepath:
                    p.downloaded_path = filepath
                    p.save()

                    if destroy_favorited_status(status):
                        continue
                else:
                    logger.error('Download photo failed?')

def fetch_favorites(max_id=None):
    statuses = None

    try:
        logger.info('Request start with: %s' % (str(max_id) or 'latest'))
        statuses = api.GetFavorites(count=100, max_id=max_id)
        logger.info('Request completed with %d status(es)', len(statuses) if statuses else 0)
    except twitter.TwitterError as e:
        logger.exception(e)

        if e.args[0][0]['code'] == 88:
            # TwitterError: Rate limit exceeded.
            # https://developer.twitter.com/en/docs/basics/rate-limiting

            # Let's try it in next hour later.
            logger.info('Start sleeping')
            sleep(24 * 60 * 60)
            logger.info('End sleeping')

            fetch_favorites(max_id)
    except Exception as e:
        logger.exception(e)

    if statuses and len(statuses) > 0:
        save_statuses(statuses)
        logger.info('Save completed!')

        last_id = statuses[-1].id

        if last_id == max_id:
            logger.info('This should be the end.')
            return

        fetch_favorites(last_id)


userinfo = api.VerifyCredentials()
logger.info('Verification pass!' if userinfo else 'Verification Failed')

# status = Status.select().order_by(Status.id).first()
# fetch_favorites(max_id=status.id if status else None)
fetch_favorites()

# statuses = api.GetUserTimeline(userinfo.id)
# print_sample_entity('User status: ', statuses)

# statuses = api.GetHomeTimeline()
# print_sample_entity('Home status: ', statuses)

