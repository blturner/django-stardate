from django.contrib.auth.models import User
from django.core import serializers
from django.db import models
from django.utils import timezone

from stardate.parser import Stardate
from stardate.sync import StardateSync


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

    def save(self, *args, **kwargs):
        dropbox_auth = None
        if args:
            dropbox_auth = args[0]
        super(DropboxCommon, self).save()
        if dropbox_auth:
            self.sync_to_dropbox(dropbox_auth)

    def sync_to_dropbox(self, dropbox_auth):
        sync = StardateSync(dropbox_auth)
        sync.dropbox_client.put_file(self.path, self.content, overwrite=True)


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
    owner = models.ForeignKey(User, related_name="+")
    slug = models.SlugField()

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('post-archive-index', (), {'blog_slug': self.slug})

    def get_serialized_posts(self):
        return serializers.serialize("python", self.post_set.all(),
            fields=('title', 'publish', 'stardate', 'body'))

    def update_dropbox_file(self, dropbox_auth):
        dropbox_file = self.dropbox_file
        parser = Stardate()
        posts = self.get_serialized_posts()
        dropbox_file.content = parser.parse_for_dropbox(posts)
        dropbox_file.save(dropbox_auth)

    def save_stardate_posts(self):
        parser = Stardate()
        parsed = parser.parse(self.dropbox_file.content)
        for post in parsed:
            post['blog_id'] = self.id
            try:
                p = Post.objects.get(stardate=post.get('stardate'))
            except Post.DoesNotExist:
                p = Post(**post)
            p.__dict__.update(**post)
            try:
                p.save()
            except:
                pass


class PostManager(models.Manager):

    def published(self):
        return self.get_query_set().filter(publish__lte=timezone.now()).order_by('-publish')


class Post(models.Model):
    authors = models.ManyToManyField(User, blank=True, null=True)
    blog = models.ForeignKey(Blog)
    body = models.TextField(blank=True)
    objects = PostManager()
    publish = models.DateTimeField(blank=True, null=True, unique=True)
    slug = models.SlugField(unique=True)
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
        self.clean()
        self.clean_fields()
        self.validate_unique()
        super(Post, self).save(*args, **kwargs)

        dropbox_auth = self.blog.owner.social_auth.get(provider='dropbox')
        self.blog.update_dropbox_file(dropbox_auth)

    @models.permalink
    def get_absolute_url(self):
        self.publish = self.publish.astimezone(timezone.get_current_timezone())
        return ('post-detail', (), {
            'blog_slug': self.blog.slug,
            'year': self.publish.year,
            'day': self.publish.day,
            'month': self.publish.strftime('%b').lower(),
            'post_slug': self.slug})

    def get_next_post(self):
        next = Post.objects.published().filter(publish__gt=self.publish,
            blog__exact=self.blog.id).exclude(id__exact=self.id).order_by('publish')
        if next:
            return next[0]
        return False

    def get_prev_post(self):
        prev = Post.objects.published().filter(publish__lt=self.publish,
            blog__exact=self.blog.id).exclude(id__exact=self.id).order_by('-publish')
        if prev:
            return prev[0]
        return False
