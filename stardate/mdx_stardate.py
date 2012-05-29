import markdown

from stardate.models import Blog, Post


class SDSetextHeaderProcessor(markdown.blockprocessors.SetextHeaderProcessor):
    def run(self, parent, blocks):
        lines = blocks.pop(0).split('\n')
        h = markdown.etree.SubElement(parent, 'h1')
        h.text = lines[0].strip()
        content = '\n'.join(lines[2:])
        # self.configs[0][1] stores the blog_id
        _save_or_update_post(self.configs[0][1], h.text, content)


class MyPreprocessor(markdown.preprocessors.Preprocessor):
    def run(self, lines):
        return lines


class MyTreeprocessor(markdown.treeprocessors.Treeprocessor):
    def run(self, root):
        return root


class StardateExtension(markdown.Extension):
    def __init__(self, configs):
        self.configs = configs

    def extendMarkdown(self, md, md_globals):
        sdsetextheaderprocessor = SDSetextHeaderProcessor(md)
        sdsetextheaderprocessor.configs = self.configs
        md.parser.blockprocessors.add('sdsetextheaderprocessor', sdsetextheaderprocessor, '_begin')
        # md.preprocessors.add('mypreprocessor', MyPreprocessor(md), '_begin')
        # md.treeprocessors.add('mytreeprocessor', MyTreeprocessor(md), '_begin')


def makeExtension(configs=None):
    return StardateExtension(configs=configs)


def _save_or_update_post(blog_id, title, content=None):
    p, created = Post.objects.get_or_create(title=title,
        blog=Blog.objects.get(id=blog_id))
    p.title = title
    p.content = content
    p.save()
