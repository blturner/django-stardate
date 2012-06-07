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
import re

from django.template.defaultfilters import slugify


TAB_LENGTH = 4
STX = u'\u0002'  # Use STX ("Start of text") for start-of-placeholder
ETX = u'\u0003'  # Use ETX ("End of text") for end-of-placeholder


class Parser(object):
    def __init__(self, parser=None):
        self.parser = parser
        self.parser.processors['setextheader'] = SetextHeaderProcessor(self.parser)
        self.parser.processors['emptyblock'] = EmptyBlockProcessor(self.parser)

    def parse(self, source):
        self.lines = source.split("\n")
        return self.parser.parseDocument(self.lines)


class BlockParser(object):
    def __init__(self):
        self.processors = dict()

    def parseDocument(self, lines):
        self.bits = []
        self.parseChunk('\n'.join(lines))
        return self.bits

    def parseChunk(self, text):
        self.parseBlocks(text.split('\n\n'))
        # import pdb; pdb.set_trace()

    def parseBlocks(self, blocks):
        blocks = filter(None, blocks)
        while blocks:
            for processor in self.processors.values():
                if processor.test(blocks[0]):
                    processor.run(blocks)
                    break


class Processor(object):
    """ Base processor class. """
    def __init__(self, parser=None):
        self.parser = parser

    def test(self, block):
        pass

    def run(self, blocks):
        pass


class SetextHeaderProcessor(Processor):
    RE = re.compile(r'^.*?\n[=-]{3,}', re.MULTILINE)

    def test(self, block):
        return bool(self.RE.match(block))

    def run(self, blocks):
        post = {}
        lines = blocks.pop(0).split('\n')
        post['title'] = lines[0].strip()
        post['content'] = '\n'.join(lines[2:])
        self.parser.bits.append(post)


class EmptyBlockProcessor(Processor):
    RE = re.compile(r'^\s*\n')

    def test(self, block):
        return bool(self.RE.match(block))

    def run(self, blocks):
        blocks.pop(0)
        print "Removed empty block."


def parse_file(source, parser=BlockParser()):
    parser = Parser(parser=parser)

    if not source.strip():
        return u""
    try:
        source = unicode(source)
    except UnicodeDecodeError:
        raise Exception

    source = source.replace(STX, "").replace(ETX, "")
    source = source.replace("\r\n", "\n").replace("\r", "\n") + "\n\n"
    source = re.sub(r'\n\s+\n', '\n\n', source)
    source = source.expandtabs(TAB_LENGTH)

    root = parser.parse(source)

    posts = []
    for post in root:
        attrs = {}
        attrs['title'] = post.get('title')
        attrs['slug'] = slugify(attrs['title'])

        lines = post.get('content').split('\n')
        for line in lines:
            attr = _metadata(line)
            if attr:
                attrs[attr] = line.split(':')[1].strip()
        attrs['body'] = '\n'.join([line for line in lines if not _metadata(line)])
        posts.append(attrs)
    return posts


def _metadata(string):
    attr = None
    RE = re.compile(r'^!\[(?P<attr>\w+)?\]:')
    try:
        attr = RE.match(string).group('attr')
    except:
        pass
    return attr
