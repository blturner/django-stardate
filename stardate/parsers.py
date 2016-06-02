import datetime
import logging
import pytz
import types
import yaml

from django.utils.timezone import is_aware, make_aware, utc

from dateutil import tz
from dateutil.parser import parse

from stardate.backends import BaseStardateParser

logger = logging.getLogger(__name__)

DELIMITER = "\n---\n\n"
TIMEFORMAT = '%Y-%m-%d %I:%M %p'  # 2012-01-01 09:00 AM


class FileParser(BaseStardateParser):
    def __init__(self):
        self.delimiter = DELIMITER
        self.timeformat = TIMEFORMAT

    def render(self, post):
        """
        Turn a post dictionary into a rendered string
        """
        post = post.copy()

        # Body gets processed separately
        body = post.pop('body')

        # Generate meta data lines
        # One key/value pair per line
        meta = []
        for key in sorted(post.keys()):
            try:
                value = post[key]

                if value:
                    if isinstance(value, datetime.datetime):
                        value = datetime.datetime.strftime(value, '%Y-%m-%d %I:%M %p %z')
                    field_string = '{0}: {1}'.format(key, value)
                    meta.append(field_string)
            except KeyError:
                pass
        meta = '\n'.join(meta)

        # Body is separated from meta by three lines
        rendered = '{0}\n\n\n{1}'.format(meta, body)
        return rendered

    def pack(self, posts):
        """
        Render a list of post dictionaries to a single string
        """
        post_list = []

        for post in posts:
            post_list.append(self.render(post))

        document = self.delimiter.join(post_list)
        return document

    def parse(self, string):
        """
        Parse a single string into a dictionary representing a post object.
        """
        if not len(string) > 0:
            logger.warn('parser received an empty string')
            return None

        # split each string from it's meta data
        bits = string.split('\n\n\n')

        if not len(bits) > 1:
            logger.warn('Not enough information found to parse string.')
            return None

        # load meta data into post dictionary
        post_data = yaml.load(bits[0]) or {}

        # post body is everything else
        # Join incase other parts of post are separated
        # by three return characters \n\n\n

        if isinstance(post_data, dict):
            post_data['body'] = ''.join(bits[1:])

        try:
            timezone = post_data['timezone']
        except KeyError:
            timezone = None

        if 'publish' in post_data:
            post_data['publish'] = self.parse_publish(post_data['publish'], timezone)

        if 'timezone' not in post_data and 'publish' in post_data:
            post_data['timezone'] = datetime.datetime.strftime(post_data['publish'], '%Z')
        return post_data

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
        parsed_list = []

        for post in string.split(self.delimiter):
            parsed = self.parse(post)
            if parsed:
                parsed_list.append(parsed)
        return parsed_list
