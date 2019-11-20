from peewee import *
from json import dumps
from config import DATABASE_FILE
from twitter.models import *
from logger import getLogger

import logging

_db = SqliteDatabase(DATABASE_FILE)
logger = getLogger(__name__)


def pretty_json_string(dic):
    return dumps(dic, sort_keys=True, indent=4)


class User(Model):
    id = BigIntegerField(primary_key=True)
    name = CharField(null=True)
    created_at = CharField(null=True)
    followers = IntegerField(null=True)
    statuses_count = IntegerField(null=True)
    location = CharField(null=True)
    screen_name = CharField(null=True)
    profile_image_url = CharField(null=True)
    description = CharField(null=True)

    class Meta:
        database = _db

    def __str__(self):
        return 'id: %s, username: %s' % (self.id, self.name)

    @classmethod
    def initialize(cls, user):
        u, _ = cls.get_or_create(id=user.id)
        u.name = user.name
        u.created_at = user.created_at
        u.followers = user.followers_count
        u.statuses_count = user.statuses_count
        u.location = user.location
        u.screen_name = user.screen_name
        u.profile_image_url = user.profile_image_url
        u.description = user.description

        u.save()
        return u

class Video(Model):
    id = BigIntegerField(primary_key=True)
    display_url = CharField(null=True)
    expanded_url = CharField(null=True)
    media_url = CharField(null=True)
    media_url_https = CharField(null=True)
    size = CharField(null=True)
    url = CharField(null=True)
    content_type = CharField(null=True)
    video_url = CharField(null=True)
    bitrate = IntegerField(null=True)
    duration_millis = IntegerField(null=True)
    aspect_ratio = CharField(null=True)
    downloaded_path = CharField(null=True)

    class Meta:
        database = _db

    def __str__(self):
        return 'id: %s, url: %s' % (self.id, self.media_url_https)

    @classmethod
    def initialize(cls, video):
        v, _ = cls.get_or_create(id=video.id)
        v.display_url = video.display_url
        v.expanded_url = video.expanded_url
        v.media_url = video.media_url
        v.media_url_https = video.media_url_https
        v.size = pretty_json_string(video.sizes)
        v.url = video.url

        info_dict = video.video_info
        v.duration_millis = info_dict['duration_millis']
        v.aspect_ratio = str(info_dict['aspect_ratio'])

        prefer_variant = None

        for variant in info_dict['variants']:
            if 'bitrate' not in variant:
                continue

            if prefer_variant is None:
                prefer_variant = variant
            else:
                if variant['bitrate'] > prefer_variant['bitrate']:
                    prefer_variant = variant

        v.content_type = prefer_variant['content_type']
        v.video_url = prefer_variant['url']
        v.bitrate = prefer_variant['bitrate']

        v.save()
        return v

class Photo(Model):
    id = BigIntegerField(primary_key=True)
    display_url = CharField(null=True)
    expanded_url = CharField(null=True)
    media_url = CharField(null=True)
    media_url_https = CharField(null=True)
    size = CharField(null=True)
    url = CharField(null=True)
    downloaded_path = CharField(null=True)

    class Meta:
        database = _db

    def __str__(self):
        return 'id: %s, url: %s' % (self.id, self.media_url_https)

    @classmethod
    def initialize(cls, photo):
        p, _ = cls.get_or_create(id=photo.id)
        p.display_url = photo.display_url
        p.expanded_url = photo.expanded_url
        p.media_url = photo.media_url
        p.media_url_https = photo.media_url_https
        p.size = pretty_json_string(photo.sizes)
        p.url = photo.url

        p.save()
        return p

class Status(Model):
    id = BigIntegerField(primary_key=True)
    text = CharField(null=True)
    lang = CharField(null=True)
    possibly_sensitive = BooleanField(null=True)
    favorited = BooleanField(null=True)
    retweet_count = IntegerField(null=True)
    favorite_count = IntegerField(null=True)
    source = CharField(null=True)
    created_at = CharField(null=True)

    user = ForeignKeyField(User, backref='statuses', null=True)
    video = ForeignKeyField(Video, backref='statuses', null=True)
    photos = ManyToManyField(Photo, backref='statuses')

    class Meta:
        database = _db

    def __str__(self):
        return 'id: %s, user: %s, text: %s' % (self.id, self.user.name, self.text)

    @classmethod
    def initialize(cls, status):
        s, _ = cls.get_or_create(id=status.id)
        s.text = status.text
        s.lang = status.lang
        s.possibly_sensitive = status.possibly_sensitive
        s.favorited = status.favorited
        s.retweet_count = status.retweet_count
        s.favorite_count = status.favorite_count
        s.source = status.source
        s.created_at = status.created_at
        s.user = User.initialize(status.user)

        if status.media:
            s.photos.clear()

            for media in status.media:
                if media.type == 'video':
                    s.video = Video.initialize(media)
                elif media.type == 'photo':
                    s.photos.add(Photo.initialize(media))
                else:
                    logger.warning('Unexpected media type: %s!' % media.type)

        s.save()
        return s

    def is_video(self):
        return self.video != None

    def is_photo(self):
        return self.photos.count() > 0

_db.connect()
_db.create_tables([
    User,
    Video,
    Photo,
    Status,
    Status.photos.get_through_model(),
])
