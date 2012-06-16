"""
Django Stardate Parser
======================

Simplified version of Python-Markdown's parser implementation. This version is
designed to parse a markdown-formatted file and split it's syntax up into a
Stardate Post model.

## Python-Markdown, https://github.com/waylan/Python-Markdown

Copyright 2007, 2008 The Python Markdown Project (v. 1.7 and later)
Copyright 2004, 2005, 2006 Yuri Takhteyev (v. 0.2-1.6b)
Copyright 2004 Manfred Stienstra (the original version)
"""
import datetime
import yaml

from django.template.defaultfilters import slugify


TAB_LENGTH = 4
STX = u'\u0002'  # Use STX ("Start of text") for start-of-placeholder
ETX = u'\u0003'  # Use ETX ("End of text") for end-of-placeholder


class Parser(object):
    def __init__(self, parser=None):
        self.parser = parser
        # self.parser.processors['default'] = DefaultProcessor(self.parser)
        # self.parser.processors['setextheader'] = SetextHeaderProcessor(self.parser)

    def parse(self, source):
        self.lines = source.split("\n---\n")
        return self.parser.parseDocument(self.lines)


class BlockParser(object):
    def __init__(self):
        self.processors = dict()

    def parseDocument(self, lines):
        self.bits = []
        self.parseChunk(lines)
        return self.bits

    def parseChunk(self, text):
        for post in text:
            bits = post.split('\n\n\n')
            data = yaml.load(bits[0])

            data['body'] = bits[1]
            data['publish'] = datetime.datetime.strptime(data['publish'], '%m/%d/%Y')
            data['slug'] = slugify(data['title'])
            data['stardate'] = int(data['stardate'])

            self.bits.append(data)

    # def parseBlocks(self, blocks):
    #     blocks = filter(None, blocks)
    #     while blocks:
    #         for processor in self.processors.values():
    #             if processor.test(blocks[0]):
    #                 processor.run(blocks)
    #                 break


class Processor(object):
    """ Base processor class. """
    def __init__(self, parser=None):
        self.parser = parser

    def test(self, block):
        pass

    def run(self, blocks):
        pass


def reverse_parse(post, dropbox):
    post_obj = post

    posts = dropbox.content.split('\n---\n')
    new_posts = []
    for post in posts:
        bits = post.split('\n\n\n')
        data = yaml.load(bits[0])
        if data['stardate'] == post_obj.stardate:
            bits[1] = post_obj.body
        new_posts.append('\n\n\n'.join(bits))
    return '\n---\n'.join(new_posts)


def parse_file(source, parser=BlockParser()):
    parser = Parser(parser=parser)

    if not source.strip():
        return u""
    try:
        source = unicode(source)
    except UnicodeDecodeError:
        raise Exception

    source = source.replace(STX, "").replace(ETX, "")
    # source = source.replace("\r\n", "\n").replace("\r", "\n") + "\n\n"
    # source = re.sub(r'\n\s+\n', '\n\n', source)
    source = source.expandtabs(TAB_LENGTH)

    return parser.parse(source)
