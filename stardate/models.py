from django.contrib.auth.models import User
from django.core import serializers
from django.db import models
from django.utils import timezone

from social_auth.models import UserSocialAuth
from markupfield.fields import MarkupField

from stardate.backends import get_backend
from django.conf import settings


class Blog(models.Model):
    authors = models.ManyToManyField(User, blank=True, null=True)
    # Dot notation path to backend Class
    backend_class = models.CharField(
        max_length=255,
        blank=True,
        default=settings.STARDATE_BACKEND
    )
    # Path to file or directory used by backend to determine
    # how and where to store / retrieve posts
    backend_file = models.CharField(blank=True, max_length=255)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, related_name="+")
    slug = models.SlugField()
    social_auth = models.ForeignKey(UserSocialAuth, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Blog, self).__init__(*args, **kwargs)
        # Instantiate the backend
        self.backend = get_backend(self.backend_class)
        # If backend uses a social auth to connect,
        # initialize it here
        try:
            self.backend.set_social_auth(self.social_auth)
        except:
            pass

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('post-archive-index', (), {'blog_slug': self.slug})

    def get_backend_choice(self):
        choices = self.backend.get_source_list()
        return choices[int(self.backend_file)][1]

    def get_serialized_posts(self):
        """
        Returns a list of dictionaries representing post objects on the blog.
        """
        return serializers.serialize("python", self.post_set.filter(
            deleted=False), fields=('title', 'publish', 'stardate', 'body'))

    def get_backend_posts(self):
        path = self.get_backend_choice()
        return self.backend.get_posts(path)

    def save_post_objects(self, post_list):
        for post in post_list:
            post['blog_id'] = self.id
            try:
                p = Post.objects.get(stardate=post.get('stardate'))
            except Post.DoesNotExist:
                p = Post(**post)
            p.__dict__.update(**post)
            p.save()
            print 'Saved: %s' % p.title

    def sync_backend(self):
        post_list = self.get_serialized_posts()
        path = self.get_backend_choice()
        self.backend.sync(path, post_list)


class PostManager(models.Manager):

    def published(self):
        return self.get_query_set().filter(
            deleted=False,
            publish__lte=timezone.now()).order_by('-publish')


class Post(models.Model):
    authors = models.ManyToManyField(User, blank=True, null=True)
    blog = models.ForeignKey(Blog)
    body = MarkupField(default_markup_type='markdown')
    deleted = models.BooleanField()
    objects = PostManager()
    publish = models.DateTimeField(blank=True, null=True, unique=True)
    slug = models.SlugField()
    stardate = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ['-publish']

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        # Post must use the same backend as the Blog
        self.backend = self.blog.backend

    def __unicode__(self):
        return self.title

    def clean(self, *args, **kwargs):
        import uuid
        from django.template.defaultfilters import slugify

        if not self.stardate:
            self.stardate = str(uuid.uuid1())
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.body.raw.endswith('\n'):
            self.body.raw += '\n'

    def mark_deleted(self):
        self.deleted = True
        return self

    def save(self, push=True, *args, **kwargs):
        # Validate first so things don't break on pusn
        self.clean()
        self.clean_fields()
        self.validate_unique()

        if push:
            # Initialize our backend with user's social auth
            self.backend.set_social_auth(self.blog.social_auth)
            # Sync this post with our backend
            self.backend.push([self])
        super(Post, self).save(*args, **kwargs)

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
        next = Post.objects.published().filter(
            publish__gt=self.publish, blog__exact=self.blog.id).exclude(
                id__exact=self.id).order_by('publish')
        if next:
            return next[0]
        return False

    def get_prev_post(self):
        prev = Post.objects.published().filter(
            publish__lt=self.publish, blog__exact=self.blog.id).exclude(
                id__exact=self.id).order_by('-publish')
        if prev:
            return prev[0]
        return False
