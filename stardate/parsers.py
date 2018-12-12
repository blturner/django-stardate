import datetime
import logging
import pytz
import re
import types
import yaml

from django.utils.timezone import is_aware, make_aware, utc

import frontmatter
from dateutil import tz
from dateutil.parser import parse

from stardate.backends import BaseStardateParser
from stardate.utils import get_post_model


logger = logging.getLogger(__name__)

DELIMITER = "\n\n==========\n\n"
TIMEFORMAT = '%Y-%m-%d %I:%M %p'  # 2012-01-01 09:00 AM


class StardateHandler(frontmatter.default_handlers.YAMLHandler):
    FM_BOUNDARY = re.compile(r'^\n{2}', re.MULTILINE)
    START_DELIMITER = ''
    END_DELIMITER = ''


class FileParser(BaseStardateParser):
    def __init__(self):
        self.delimiter = DELIMITER
        self.timeformat = TIMEFORMAT

    def pack(self, posts):
        """
        Render a list of post dictionaries to a single string
        """
        post_list = []

        for post in posts:
            try:
                if isinstance(post, dict):
                    Post = get_post_model()

                    if getattr(post, 'content'):
                        post.pop('content')

                    post = Post(**post)
                post_list.append(post.to_string())
            except AttributeError:
                if isinstance(post, frontmatter.Post):
                    body = post.content

                    if 'publish' in post.keys():
                        post['publish'] = datetime.datetime.strftime(
                            self.parse_publish(post.get('publish')),
                            '%Y-%m-%d %I:%M %p %z'
                        )
                else:
                    body = post.pop('body', None)

                    if not body:
                        body = post.pop('content', None)

                    if 'content' in post:
                        post.pop('content')

                    if post.get('publish'):
                        post['publish'] = datetime.datetime.strftime(
                            self.parse_publish(post.get('publish')), '%Y-%m-%d %I:%M %p %z'
                        )

                post_list.append(frontmatter.dumps(frontmatter.Post(body, **post)))

        return self.delimiter.join(post_list)

    def parse(self, string):
        """
        Parse a single string into a dictionary representing a post object.
        """
        if not len(string) > 0:
            logger.warn('parser received an empty string')
            return None

        post = frontmatter.loads(string)

        if not post.metadata:
            logger.warn('Not enough information found to parse string.')
            return None

        try:
            timezone = post.get('timezone')
        except KeyError:
            timezone = None

        if post.get('publish'):
            post.metadata['publish'] = self.parse_publish(post.get('publish'), timezone)

        if 'timezone' not in post.keys() and 'publish' in post.keys():
            post.metadata['timezone'] = datetime.datetime.strftime(post.get('publish'), '%Z')

        return post

    def parse_publish(self, date, timezone=None):
        """
        Parses a datetime string into a datetime instance.
        """
        if type(date) is datetime.date:
            date = datetime.datetime.combine(date, datetime.datetime.min.time())

        if not isinstance(date, datetime.datetime):
            date = parse(date)

        if not is_aware(date) and timezone:
            date = date.replace(tzinfo=tz.gettz(timezone))

        if not is_aware(date):
            try:
                # Django>1.7
                date = make_aware(date)
            except TypeError:
                # Django<1.8
                date = make_aware(date, utc)

        if timezone and date.tzinfo != tz.gettz(timezone):
            date = date.replace(tzinfo=tz.gettz(timezone))

        return date

    def unpack(self, string):
        """
        Returns a list of parsed post dictionaries.
        """
        posts = string.split(self.delimiter)
        unpacked = []

        for post in posts:
            parsed = self.parse(post)
            if parsed:
                unpacked.append(parsed)

        return unpacked
