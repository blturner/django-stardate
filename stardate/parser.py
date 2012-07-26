import datetime
import yaml

from dateutil.parser import parse
from django.utils.timezone import get_current_timezone, make_aware, utc

DELIMITER = "\n---\n"
TIMEFORMAT = '%Y-%m-%d %I:%M %p'  # 2012-01-01 09:00 AM
current_timezone = get_current_timezone()


class Stardate(object):
    def __init__(self):
        self.parser = PostParser()

    def parse(self, text):
        return self.parser.parse_text(text)

    def parse_for_dropbox(self, posts):
        return self.parser.format_for_dropbox(posts)


class PostParser(object):
    def __init__(self):
        self.delimiter = DELIMITER
        self.processors = {}

    def parse_text(self, text):
        self.parsed_posts = []

        for post in text.split(self.delimiter):
            self.parsed_posts.append(self.parse_post(post))
        return self.parsed_posts

    def parse_post(self, post):
        try:
            bits = post.split('\n\n\n')
            post_data = yaml.load(bits[0])
            post_data['body'] = bits[1]
        except:
            post_data = {}

        if post_data.get('publish'):
            if not isinstance(post_data['publish'], datetime.datetime):
                post_data['publish'] = parse(post_data['publish'])
                post_data['publish'] = make_aware(post_data['publish'], current_timezone).astimezone(utc)
        return post_data

    def format_for_dropbox(self, posts):
        processed_posts = []
        for post in posts:
            processed_post = ['']
            fields = post.get('fields')

            try:
                fields['publish'] = fields['publish'].astimezone(current_timezone)
                fields['publish'] = datetime.datetime.strftime(fields['publish'], TIMEFORMAT)
            except:
                pass

            body = fields.pop('body')

            for k, v in fields.items():
                if v:
                    processed_post[0] += "%s: %s\n" % (k, v)
            processed_post.insert(1, body)
            processed_posts.append('\n\n'.join(processed_post))
        return '\n---\n\n'.join(processed_posts)
