#!/usr/bin/env python

import coloredlogs, logging, logging.config
import twitter
import click
from os.path import split
from time import sleep

from twitter_cli.config import *
from twitter_cli.models import *
from twitter_cli.downloader import *
from twitter_cli.counter import *

from requests.exceptions import SSLError

# Refer to
#   1. https://stackoverflow.com/a/7507842/1677041
#   2. https://stackoverflow.com/a/49400680/1677041
#   3. https://docs.python.org/2/library/logging.config.html
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'colored': {
            '()': 'coloredlogs.ColoredFormatter',
            'format': "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            'datefmt': '%H:%M:%S',
        }
    },
    'handlers': {
        'default': {
            'level': 'DEBUG' if __debug__ else 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'console': {
            'level': 'DEBUG' if __debug__ else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': 'main.log',
            'maxBytes': 1024 * 1024,
            'backupCount': 10
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'twitter_cli.downloader': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'twitter': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'twitter_cli': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

api = twitter.Api(proxies=get_proxy(), **get_keys())

PAGE_SIZE = 100
MYSELF = 'me'

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

def destroy_favorited_status(status, retry=10):
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
    except SSLError as e:
        if retry > 0:
            return destroy_favorited_status(status, retry=retry-1)
        else:
            raise e

    return False

def save_status(status, destroy=False, timeline=None):
    if isinstance(status, TwitterModel):
        s = Status.initialize(status)
    elif isinstance(status, PeeweeModel):
        s = status
    else:
        assert('Unexpected status type! %s' % status)

    logger.debug('Status: %s\n%s:[\n%s\n]' % (s.id, s.user.name, s.text))

    should_destory = False
    video = s.video

    if video:
        logger.debug('Found video: %s' % video)
        path = get_video_storage_path(is_favorite=s.favorited, timeline=timeline)
        extension = split(video.content_type)[-1]
        filepath = download_video(video.video_url, path, prefix=str(status.id), extension=extension)

        if filepath:
            video.downloaded_path = filepath
            video.save()

            should_destory = True
            Counter.success()
        else:
            logger.error('Download video failed?')
            Counter.failure()

    if s.is_photo:
        for p in s.photos:
            logger.debug('Found photo: %s' % p)
            path = get_photo_storage_path(is_favorite=s.favorited, timeline=timeline)
            filepath = download_photo(p.media_url_https or p.media_url, path, prefix=str(status.id))

            if filepath:
                p.downloaded_path = filepath
                p.save()

                should_destory = True
                Counter.success()
            else:
                logger.error('Download photo failed?')
                Counter.failure()

    if s.quoted_status:
        logger.debug('Found quoted status: %s\n%s:[\n%s\n]' % (s.quoted_status.id, s.quoted_status.user.name, s.quoted_status.text))
        save_status(s.quoted_status)

        should_destory = True

    if s.retweeted_status:
        logger.debug('Found retweeted status: %s\n%s:[\n%s\n]' % (s.retweeted_status.id, s.retweeted_status.user.name, s.retweeted_status.text))
        save_status(s.retweeted_status)

        should_destory = True

    if destroy:
        if not should_destory:
            logger.warning('Destroying this status even no media found!%s', print_sample_entity(s, 'Details:\n'))

        destroy_favorited_status(status)

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
            code = e.args[0][0]['code']

            if code == 88:
                # TwitterError: Rate limit exceeded.
                # https://developer.twitter.com/en/docs/basics/rate-limiting

                # Let's try it in next hour later.
                logger.info('Start sleeping because rate limit exceeded')
                sleep(2 * 60 * 60)
                logger.info('End sleeping')

                continue
            elif code == 34:
                # "Sorry, that page does not exist."
                break
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
@click.option('--debug/--no-debug', default=False, help='Enable logger level to DEBUG')
@click.pass_context
def cli(ctx, debug):
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    debug and click.echo('Debug mode is on')

@cli.command()
@click.pass_context
def configure(ctx):
    '''
    Show the current configurations.
    '''
    logger.info('\n%s' % get_raw_config())

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
        print_sample_entity(userinfo, 'User info:')
        logger.info('Verification pass!')
    else:
        logger.error('Verification Failed')

@cli.command()
@click.argument('usernames', nargs=-1, type=click.STRING)
@click.option('--pinned/--no-pinned', default=False, help='Append the pinned users to current usernames')
@click.option('--download-media/--no-download-media', default=True, help='Download status\'s media files or not')
@click.option('--schedule', type=click.INT, default=0, help='Run as scheduler with specified hours')
@click.pass_context
def timeline(ctx, usernames, pinned, download_media, schedule):
    '''
    Fetch the specified users' timeline.
    '''
    # Convert the tuple to list
    usernames = list(usernames)

    if pinned:
        usernames.extend(get_pinned_users())
    if len(usernames) <= 0:
        usernames = [MYSELF]

    def job():
        generators = {}

        for username in usernames:
            if username == MYSELF:
                pfunc = lambda max_id: api.GetHomeTimeline(count=PAGE_SIZE, max_id=max_id)
            elif len(username) > 0:
                pfunc = lambda max_id: api.GetUserTimeline(screen_name=username, count=PAGE_SIZE, max_id=max_id)
            else:
                pfunc = None

            if pfunc:
                generators[username] = fetch_iteriable_statuses(pfunc)

        for username, generator in generators.items():
            logger.info('Fetching timeline of pinned user [%s]' % username)

            for status in generator:
                shall_download = status.favorite_count * 1.0 / status.user.followers_count > 0.05
                shall_download |= status.user.retweet_count * 1.0 / status.user.followers_count > 0.01

                if shall_download or download_media:
                    save_status(status, timeline=username)
                else:
                    print_sample_entity(status, prefix='Info:')

    if schedule <= 0:
        job()
    else:
        while True:
            try:
                job()
            except (KeyboardInterrupt, SystemExit):
                logger.warning('Interrupt by keyboard, stopping')
                break
            except Exception as e:
                logger.exception(e)

            logger.info('Start sleeping, waiting for next schedule...')
            sleep(schedule * 60 * 60)
            logger.info('End sleeping')

    logger.info('Done!')

@cli.command()
@click.option('--from-latest/--from-last', default=False, help='Fetch statuses from latest or last saved one')
@click.option('--download-media/--no-download-media', default=True, help='Download status\'s media files or not')
@click.option('--destroy/--no-destroy', default=False, help='Destroy the favorite statuses')
@click.option('--schedule', type=click.INT, default=0, help='Run as scheduler with specified hours')
@click.pass_context
def favorites(ctx, from_latest, download_media, destroy, schedule):
    '''
    Fetch the user's favorite statuses.
    '''

    def job():
        if from_latest:
            max_id = None
        else:
            status = Status.select().order_by(Status.id).first()
            max_id = status.id if status else None

        for status in fetch_iteriable_statuses(lambda max_id: api.GetFavorites(count=PAGE_SIZE, max_id=max_id)):
            if download_media:
                save_status(status, destroy=destroy)
            else:
                print_sample_entity(status, prefix='Info: ')

    if schedule <= 0:
        job()
    else:
        while True:
            try:
                job()
            except (KeyboardInterrupt, SystemExit):
                logger.warning('Interrupt by keyboard, stopping')
                break
            except Exception as e:
                logger.exception(e)

            logger.info('Start sleeping, waiting for next schedule...')
            sleep(schedule * 60 * 60)
            logger.info('End sleeping')

    wait_for_download_completed()
    logger.info('Done!')

@cli.command()
@click.argument('names', nargs=-1, type=click.STRING)
@click.option('--username', type=click.STRING, default=None, help='List owner\'s screen name')
@click.option('--download-media/--no-download-media', default=True, help='Download status\'s media files or not')
@click.pass_context
def list(ctx, names, username, download_media,):
    '''
    Fetch the statuses of specified list.
    '''
    tweet_lists = api.GetLists(screen_name=username)

    if len(names) > 0:
        tweet_lists = tweet_lists.filter(lambda x: x.name in names)

    if len(tweet_lists) <= 0:
        logger.warn("Not found expected list!")
        return

    for tweet_list in tweet_lists:
        for status in fetch_iteriable_statuses(lambda max_id: api.GetListTimeline(list_id=tweet_list.id, count=PAGE_SIZE, max_id=max_id)):
            if download_media:
                save_status(status, destroy=False)
            else:
                print_sample_entity(status, prefix='Info: ')

if __name__ == '__main__':
    cli()
