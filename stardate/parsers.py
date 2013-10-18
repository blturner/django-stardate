import datetime
import uuid
import yaml

from dateutil.parser import parse
from django.utils.timezone import get_current_timezone, make_aware, utc

from stardate.backends import BaseStardateParser

DELIMITER = "\n---\n"
TIMEFORMAT = '%Y-%m-%d %I:%M %p'  # 2012-01-01 09:00 AM
current_timezone = get_current_timezone()


class FileParser(BaseStardateParser):
    def __init__(self):
        self.delimiter = DELIMITER
        self.timeformat = TIMEFORMAT

    def render(self, post):
        """
        Turn a post dictionary into a rendered string
        """
        post = post.copy()

        # FIXME?: this belongs in serialization process
        try:
            post['publish'] = post['publish'].astimezone(current_timezone)
            post['publish'] = datetime.datetime.strftime(post['publish'], self.timeformat)
        except:
            pass

        # Body gets processed separately
        body = post.pop('body')

        # Generate meta data lines
        # One key/value pair per line
        meta = []
        for key in sorted(post.keys()):
            try:
                value = post[key]
                if value:
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
        try:
            # split each string from it's meta data
            bits = string.split('\n\n\n')

            # load meta data into post dictionary
            post_data = yaml.load(bits[0])

            # post body is everything else
            # Join incase other parts of post are separated
            # by three return characters \n\n\n
            post_data['body'] = ''.join(bits[1:])
        except:
            post_data = {}

        # FIXME: this belongs in deserialization, perhaps
        # on model?
        if 'publish' in post_data:
            if not isinstance(post_data['publish'], datetime.datetime):
                post_data['publish'] = parse(post_data['publish'])
                post_data['publish'] = make_aware(post_data['publish'], current_timezone).astimezone(utc)
        return post_data

    def unpack(self, string):
        """
        Returns a list of parsed post dictionaries.
        """
        self.parsed_list = []

        for post in string.split(self.delimiter):
            if self.parse(post):
                self.parsed_list.append(self.parse(post))
        return self.parsed_list
