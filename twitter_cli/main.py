#!/usr/bin/env python

from logger import getLogger
import twitter
import click
from os.path import split
from time import sleep

from config import *
from models import *
from downloader import *

api = twitter.Api(proxies=get_proxy(), **get_keys())
logger = getLogger(__name__)

DEBUG = False
PAGE_SIZE = 100

def print_sample_entity(entities, prefix=''):
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

def save_status(status, destroy=False):
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

            if destroy and destroy_favorited_status(status):
                return
        else:
            logger.error('Download video failed?')

    if s.is_photo:
        for p in s.photos:
            logger.debug('Found photo: %s' % p)
            filepath = download_photo(p.media_url_https or p.media_url)

            if filepath:
                p.downloaded_path = filepath
                p.save()

                if destroy and destroy_favorited_status(status):
                    return
            else:
                logger.error('Download photo failed?')

    if s.retweeted_status:
        save_status(s.retweeted_status, destroy)

def fetch_iteriable_statuses(pfunc):
    max_id = None
    statuses = None

    while True:
        try:
            logger.info('Request starts with %s' % (max_id or 'latest'))
            statuses = pfunc(max_id)
            logger.info('Request completed with %d status(es)', len(statuses) if statuses else 0)
        except twitter.TwitterError as e:
            logger.exception(e)
            statuses = None

            if e.args[0][0]['code'] == 88:
                # TwitterError: Rate limit exceeded.
                # https://developer.twitter.com/en/docs/basics/rate-limiting

                # Let's try it in next hour later.
                logger.info('Start sleeping')
                sleep(24 * 60 * 60)
                logger.info('End sleeping')

                continue
        except Exception as e:
            logger.exception(e)
            statuses = None

        if statuses and len(statuses) > 0:
            for status in statuses:
                yield status

            new_max_id = statuses[-1].id

            if new_max_id == max_id:
                logger.info('This should be the normal ending.')
                break

            max_id = new_max_id
        else:
            break

@click.group()
@click.option('--debug/--no-debug', default=False)
@click.pass_context
def cli(ctx, debug):
    global DEBUG
    DEBUG = debug
    debug and click.echo('Debug mode is on')
    pass

@cli.command()
@click.pass_context
def credential(ctx):
    '''
    Verify the current user credential.
    '''

    try:
        userinfo = api.VerifyCredentials()
    except twitter.TwitterError as e:
        logger.exception(e)
        logger.error('Make sure you\'ve configured the twitter keys right in file %s.' % CONFIG_FILE)

    if userinfo:
        logger.info('Verification pass!')
        print_sample_entity(userinfo)
    else:
        logger.error('Verification Failed')

@cli.command()
@click.argument('username', type=click.STRING, default='me')
@click.option('--download-media/--no-download-media', default=True)
@click.pass_context
def timeline(ctx, username, download_media):
    '''
    Fetch the specified user's timeline.
    '''

    if username == 'me':
        generator = fetch_iteriable_statuses(lambda max_id: api.GetHomeTimeline(count=PAGE_SIZE, max_id=max_id))
    elif len(username) > 0:
        generator = fetch_iteriable_statuses(lambda max_id: api.GetUserTimeline(screen_name=username, count=PAGE_SIZE, max_id=max_id))

    for status in generator:
        # print_sample_entity(status)
        print('%d: %s'.format(status.id, status.user.name))

    logger.info('Done!')

@cli.command()
@click.option('--from-latest/--from-last', default=False)
@click.option('--download-media/--no-download-media', default=True)
@click.option('--destroy/--no-destroy', default=False)
@click.pass_context
def favorites(ctx, from_latest, download_media, destroy):
    '''
    Fetch the user's favorite statuses.
    '''

    if from_latest:
        max_id = None
    else:
        status = Status.select().order_by(Status.id).first()
        max_id = status.id if status else None

    for status in fetch_iteriable_statuses(lambda max_id: api.GetFavorites(count=PAGE_SIZE, max_id=max_id)):
        if download_media:
            save_status(status, destroy=destroy)
        else:
            print_sample_entity(status)

    logger.info('Done!')
