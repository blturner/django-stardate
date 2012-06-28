from datetime import datetime

from django.contrib.auth.models import User
from django.core import serializers
from django.db import models

from stardate.dropbox_auth import DropboxAuth
from stardate.parser import Stardate


class DropboxCommon(models.Model):
    bytes = models.IntegerField(blank=True)
    icon = models.CharField(max_length=255)
    is_dir = models.BooleanField()
    modified = models.DateTimeField(blank=True, null=True)
    path = models.CharField(max_length=255)
    rev = models.CharField(max_length=255)
    revision = models.IntegerField(blank=True, null=True)
    root = models.CharField(max_length=255)
    size = models.CharField(max_length=255)
    thumb_exists = models.BooleanField()

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.path


class DropboxFolder(DropboxCommon):
    hash = models.CharField(max_length=255)
    folder = models.ForeignKey('self', blank=True, null=True)


class DropboxFile(DropboxCommon):
    client_mtime = models.DateTimeField(blank=True, null=True)
    content = models.TextField(blank=True)
    folder = models.ForeignKey(DropboxFolder, blank=True, null=True)
    mime_type = models.CharField(max_length=255)


class Blog(models.Model):
    authors = models.ManyToManyField(User, blank=True, null=True)
    dropbox_file = models.ForeignKey(DropboxFile)
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('blog_list_view', (), {'slug': self.slug})

    def get_serialized_posts(self):
        return serializers.serialize("python", self.post_set.all())


class PostManager(models.Manager):

    def published(self):
        return self.get_query_set().filter(publish__lte=datetime.now()).order_by('-publish')


class Post(models.Model):
    authors = models.ManyToManyField(User, blank=True, null=True)
    blog = models.ForeignKey(Blog)
    body = models.TextField(blank=True)
    objects = PostManager()
    publish = models.DateTimeField(blank=True, null=True)
    slug = models.SlugField()
    stardate = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ['-publish']

    def __unicode__(self):
        return self.title

    def clean(self, *args, **kwargs):
        import uuid
        from django.template.defaultfilters import slugify

        if not self.stardate:
            self.stardate = str(uuid.uuid1())
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.body.endswith('\n'):
            self.body += '\n'

    # On save, a post should parse the dropbox blog file
    # and update the post that was changed.
    def save(self, *args, **kwargs):
        super(Post, self).save(*args, **kwargs)

        stardate = Stardate()
        posts = self.blog.get_serialized_posts()
        dbfile = self.blog.dropbox_file
        dbfile.content = stardate.parse_for_dropbox(posts)
        dbfile.save()

        client = DropboxAuth().dropbox_client
        client.put_file(dbfile.path, dbfile.content, overwrite=True)

    @models.permalink
    def get_absolute_url(self):
        return ('post_detail_view', (), {
            'blog_slug': self.blog.slug,
            'year': self.publish.year,
            'day': self.publish.day,
            'month': self.publish.strftime('%b').lower(),
            'post_slug': self.slug})
