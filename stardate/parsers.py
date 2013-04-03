import datetime
import yaml

from dateutil.parser import parse
from django.utils.timezone import get_current_timezone, make_aware, utc

from stardate.backends import BaseStardateParser

DELIMITER = "\n---\n"
TIMEFORMAT = '%Y-%m-%d %I:%M %p'  # 2012-01-01 09:00 AM
current_timezone = get_current_timezone()


class SingleFileParser(BaseStardateParser):
    def __init__(self):
        self.delimiter = DELIMITER
        self.timeformat = TIMEFORMAT

    def pack(self, posts):
        """
        Packs a list of dictionaries into a single string to be saved
        into a file.
        """
        post_list = []

        for post in posts:
            p = ['']
            fields = post.get('fields')

            try:
                fields['publish'] = fields['publish'].astimezone(current_timezone)
                fields['publish'] = datetime.datetime.strftime(fields['publish'], self.timeformat)
            except:
                pass

            body = fields.pop('body')

            for k, v in fields.items():
                if v:
                    p[0] += "%s: %s\n" % (k, v)
            p.insert(1, body)
            post_list.append('\n\n'.join(p))
        return ('%s\n' % self.delimiter).join(post_list)

    def parse(self, string):
        """
        Parse a single string into a dictionary representing a post object.
        """
        try:
            # split each string from it's yaml data
            bits = string.split('\n\n\n')

            post_data = yaml.load(bits[0])
            post_data['body'] = bits[1]
        except:
            post_data = {}

        if post_data.get('publish'):
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
            self.parsed_list.append(self.parse(post))
        return self.parsed_list
