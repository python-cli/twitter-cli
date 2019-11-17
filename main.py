#!/usr/bin/env python

from logger import getLogger
import twitter
from os.path import split

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

def paginate_favorites():
    pass

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
            else:
                logger.error('Download video failed?')

        if s.is_photo:
            for p in s.photos:
                logger.debug('Found photo: %s' % p)
                filepath = download_photo(p.media_url_https or p.media_url)

                if filepath:
                    p.downloaded_path = filepath
                    p.save()
                else:
                    logger.error('Download photo failed?')


userinfo = api.VerifyCredentials()
logger.info('Verification pass!' if userinfo else 'Verification Failed')

# statuses = api.GetUserTimeline(userinfo.id)
# print_sample_entity('User status: ', statuses)

# statuses = api.GetHomeTimeline()
# print_sample_entity('Home status: ', statuses)

statuses = api.GetFavorites(count=100)
# print_sample_entity('Favorite status: ', statuses)
logger.info('Request completed!')

save_statuses(statuses)
logger.info('Save completed!')
