import datetime
import yaml

DELIMITER = "\n---\n"
TIMEFORMAT = '%Y-%m-%d %I:%M %p'  # 2012-01-01 09:00 AM


class Stardate(object):
    def __init__(self):
        self.parser = PostParser()
        self.parser.processors['datetime'] = DatetimeProcessor()

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
        bits = post.split('\n\n')
        post_data = yaml.load(bits[0])
        post_data['body'] = bits[1]
        self.process_fields(post_data)
        return post_data

    def format_for_dropbox(self, posts):
        processed_posts = []
        for post in posts:
            processed_post = ['']
            fields = post.get('fields')
            body = fields.pop('body')
            del fields['blog']
            for k, v in fields.items():
                if v:
                    v = self.process_value(v)
                    processed_post[0] += "%s: %s\n" % (k, v)
            processed_post.insert(1, body)
            processed_posts.append('\n'.join(processed_post))
        return '\n---\n\n'.join(processed_posts)

    def process_value(self, value):
        return value

    def process_fields(self, fields):
        for processor in self.processors.values():
            if processor.test(fields):
                processor.run(fields)


class Processor(object):
    def test(self, fields):
        pass

    def run(self, fields):
        pass


class DatetimeProcessor(Processor):
    def test(self, fields):
        for field in fields.iteritems():
            try:
                fields[field[0]] = datetime.datetime.strptime(field[1], TIMEFORMAT)
            except (ValueError, TypeError):
                pass

    def run(self, field):
        print field
