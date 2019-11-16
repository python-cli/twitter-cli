#!/usr/bin/env python

import twitter
from os.path import split

from config import *
from models import *
from downloader import *

api = twitter.Api(proxies=get_proxy(), **get_keys())

def print_newline():
    print('\n%s\n' % ('-' * 80))

def print_sample_entity(prefix, entities):
    if not entities:
        entities = 'Empty'

    if type(entities) in (type, list):
        entity = entities[0] if len(entities) > 0 else ''
        print('\nCount of %s: %d' % (prefix, len(entities) if entities else 0))
    else:
        entity = entities

    if isinstance(entity, twitter.models.TwitterModel):
        content = pretty_json_string(entity.AsDict())
    elif isinstance(entity, dict):
        content = pretty_json_string(entity)
    else:
        content = str(entity)

    print(prefix + content)

def paginate_favorites():
    pass

def save_statuses(statuses):
    for status in statuses:
        s = Status.initialize(status)

        print('status: %s - %s' % (s.user.name, s.text))

        video = s.video

        if video:
            print('video: %s' % video)
            extension = split(video.content_type)[-1]
            filepath = download_video(video.video_url, extension=extension)

            if filepath:
                video.downloaded_path = filepath
                video.save()

        if s.is_photo:
            for p in s.photos:
                print('photo: %s' % p)
                filepath = download_photo(p.media_url_https or p.media_url)

                if filepath:
                    p.downloaded_path = filepath
                    p.save()
                else:
                    print('Download failed?')

        print('-' * 80)


# print_sample_entity('Credentials: ', get_keys())
# print_newline()

userinfo = api.VerifyCredentials()
print('Verification pass!' if userinfo else 'Verification Failed')
print_newline()

# statuses = api.GetUserTimeline(userinfo.id)
# print_sample_entity('User status: ', statuses)
# print_newline()

# statuses = api.GetHomeTimeline()
# print_sample_entity('Home status: ', statuses)
# print_newline()

statuses = api.GetFavorites(count=100)
# print_sample_entity('Favorite status: ', statuses)
print('Request completed!')
print_newline()

save_statuses(statuses)
print('Save completed!')

# target_user = api.GetUser(screen_name='UItachy')
# print_sample_entity('UItachy info: ', target_user)
# print_newline()
