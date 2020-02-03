import logging

from peewee import *
from twitter.models import *

from .config import pretty_json_string, DATABASE_FILE

_db = SqliteDatabase(DATABASE_FILE)
logger = logging.getLogger(__name__)


def get(self, attr, default=None):
    if hasattr(self, attr):
        return getattr(self, attr)
    else:
        return default

# Inject this safe getter method to TwitterModel class.
setattr(TwitterModel, 'get', get)

class PeeweeModel(Model):
    class Meta:
        database = _db

    @classmethod
    def initialize(cls, model):
        assert(isinstance(model, TwitterModel))

class User(PeeweeModel):
    id = BigIntegerField(primary_key=True)
    name = CharField(null=True)
    created_at = CharField(null=True)
    followers = IntegerField(null=True)
    statuses_count = IntegerField(null=True)
    location = CharField(null=True)
    screen_name = CharField(null=True)
    profile_image_url = CharField(null=True)
    description = CharField(null=True)

    def __str__(self):
        return 'id: %s, username: %s' % (self.id, self.name)

    @classmethod
    def initialize(cls, user):
        super(User, cls).initialize(user)

        u, _ = cls.get_or_create(id=user.id)
        u.name = user.get('name')
        u.created_at = user.get('created_at')
        u.followers = user.get('followers_count', 0)
        u.statuses_count = user.get('statuses_count', 0)
        u.location = user.get('location')
        u.screen_name = user.get('screen_name')
        u.profile_image_url = user.get('profile_image_url')
        u.description = user.get('description')

        u.save()
        return u

class Video(PeeweeModel):
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

    def __str__(self):
        return 'id: %s, url: %s' % (self.id, self.media_url_https)

    @classmethod
    def initialize(cls, video):
        super(Video, cls).initialize(video)

        v, _ = cls.get_or_create(id=video.id)
        v.display_url = video.get('display_url')
        v.expanded_url = video.get('expanded_url')
        v.media_url = video.get('media_url')
        v.media_url_https = video.get('media_url_https')
        v.size = pretty_json_string(video.get('sizes'))
        v.url = video.get('url')

        info_dict = video.get('video_info')
        v.duration_millis = info_dict.get('duration_millis')
        v.aspect_ratio = str(info_dict.get('aspect_ratio'))

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

class Photo(PeeweeModel):
    id = BigIntegerField(primary_key=True)
    display_url = CharField(null=True)
    expanded_url = CharField(null=True)
    media_url = CharField(null=True)
    media_url_https = CharField(null=True)
    size = CharField(null=True)
    url = CharField(null=True)
    downloaded_path = CharField(null=True)

    def __str__(self):
        return 'id: %s, url: %s' % (self.id, self.media_url_https)

    @classmethod
    def initialize(cls, photo):
        super(Photo, cls).initialize(photo)

        p, _ = cls.get_or_create(id=photo.id)
        p.display_url = photo.get('display_url')
        p.expanded_url = photo.get('expanded_url')
        p.media_url = photo.get('media_url')
        p.media_url_https = photo.get('media_url_https')
        p.size = pretty_json_string(photo.get('sizes'))
        p.url = photo.get('url')

        p.save()
        return p

class Status(PeeweeModel):
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

    # http://docs.peewee-orm.com/en/latest/peewee/models.html#self-referential-foreign-keys
    quoted_status = ForeignKeyField('self', backref='quotes', null=True)
    retweeted_status = ForeignKeyField('self', backref='retweets', null=True)

    def __str__(self):
        return 'id: %s, user: %s, text: %s' % (self.id, self.user.name, self.text)

    @classmethod
    def initialize(cls, status):
        super(Status, cls).initialize(status)

        s, _ = cls.get_or_create(id=status.id)
        s.text = status.get('text')
        s.lang = status.get('lang')
        s.possibly_sensitive = status.get('possibly_sensitive')
        s.favorited = status.get('favorited')
        s.retweet_count = status.get('retweet_count', 0)
        s.favorite_count = status.get('favorite_count', 0)
        s.source = status.get('source')
        s.created_at = status.get('created_at')
        s.user = User.initialize(status.get('user'))

        if status.get('media'):
            s.photos.clear()

            for media in status.media:
                if media.type == 'video' or media.type == 'animated_gif':
                    s.video = Video.initialize(media)
                elif media.type == 'photo':
                    s.photos.add(Photo.initialize(media))
                else:
                    logger.warning('Unexpected media type: %s! Details: %s' % (media.type, media.AsDict()))

        if status.get('quoted_status'):
            s.quoted_status = cls.initialize(status.quoted_status)

        if status.get('retweeted_status'):
            s.retweeted_status = cls.initialize(status.retweeted_status)

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
