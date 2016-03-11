import datetime
import uuid

from django.contrib.auth.models import User
from django.core import serializers
from django.db import models
from django.db.models.query import QuerySet
from django.template.defaultfilters import slugify
from django.utils import timezone

from social.apps.django_app.default.models import UserSocialAuth
from markupfield.fields import MarkupField

from django.conf import settings

from stardate.utils import get_post_model


class Blog(models.Model):
    authors = models.ManyToManyField(User, blank=True)
    # Dot notation path to backend Class
    backend_class = models.CharField(max_length=255, blank=True)
    # Path to file or directory used by backend to determine
    # how and where to store / retrieve posts
    backend_file = models.CharField(blank=True, max_length=255)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, related_name="+")
    slug = models.SlugField(unique=True)
    social_auth = models.ForeignKey(UserSocialAuth, blank=True, null=True)


    def __unicode__(self):
        return self.name

    @property
    def backend(self):
        from stardate.backends import get_backend

        backend = get_backend(self.backend_class)
        backend.set_social_auth(self.social_auth)
        return backend

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
        return serializers.serialize("python", self.get_posts().filter(
            deleted=False), fields=('title', 'publish', 'stardate', 'body'))

    def get_posts(self):
        """
        returns a queryset of related posts based on the installed
        ``Post`` model
        """
        Post = get_post_model()
        qs = QuerySet(model=Post).filter(blog=self)
        return qs

    def save_post_objects(self, post_list):
        Post = get_post_model()

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
    def drafts(self):
        """
        Returns all draft Post instances. A draft is considered to be a Post
        without a publish property.
        """
        if self.get_queryset:
            queryset_method = self.get_queryset
        else:
            queryset_method = self.qet_query_set

        return queryset_method().filter(publish=None)

    def published(self):
        if self.get_queryset:
            queryset_method = self.get_queryset
        else:
            queryset_method = self.qet_query_set

        return queryset_method().filter(
            deleted=False,
            publish__lte=timezone.now()).order_by('-publish')


class BasePost(models.Model):
    authors = models.ManyToManyField(User, blank=True, related_name="%(app_label)s_%(class)s_related")
    blog = models.ForeignKey(Blog, related_name="%(app_label)s_%(class)s_related")
    body = MarkupField(blank=True, default_markup_type='markdown')
    created = models.DateTimeField(default=timezone.now)
    deleted = models.BooleanField(default=False)
    objects = PostManager()
    publish = models.DateTimeField(blank=True, null=True)
    slug = models.SlugField()
    stardate = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    timezone = models.CharField(blank=True, max_length=255, default=settings.TIME_ZONE)

    class Meta:
        abstract = True
        app_label = 'stardate'
        ordering = ['-publish']
        unique_together = ('blog', 'slug')

    def __init__(self, *args, **kwargs):
        super(BasePost, self).__init__(*args, **kwargs)
        # Post must use the same backend as the Blog
        if hasattr(self, 'blog'):
            self.backend = self.blog.backend

    def __unicode__(self):
        return self.title

    def clean(self, *args, **kwargs):
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
        if not hasattr(self, 'backend'):
            self.backend = self.blog.backend

        # Validate first so things don't break on push
        self.clean()
        self.clean_fields()
        self.validate_unique()

        if push:
            # Initialize our backend with user's social auth
            self.backend.set_social_auth(self.blog.social_auth)
            # Sync this post with our backend
            # need a serialized post here to pass in
            self.backend.push([self])
        super(BasePost, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('post-detail', (), {
            'blog_slug': self.blog.slug, 'post_slug': self.slug})

    @models.permalink
    def get_draft_url(self):
        return ('draft-post-detail', (), {
            'blog_slug': self.blog.slug, 'post_slug': self.slug})

    @models.permalink
    def get_dated_absolute_url(self):
        publish = self.publish

        return (
            'post-detail',
            (),
            {
                'blog_slug': self.blog.slug,
                'year': publish.year,
                'day': publish.day,
                'month': publish.strftime('%b').lower(),
                'post_slug': self.slug
            }
        )

    def get_next_post(self):
        next = self.blog.get_posts().filter(publish__gt=self.publish).exclude(
            id__exact=self.id).order_by('publish')
        if next:
            return next[0]
        return False

    def get_prev_post(self):
        prev = self.blog.get_posts().filter(publish__lt=self.publish).exclude(
                id__exact=self.id).order_by('-publish')
        if prev:
            return prev[0]
        return False

    @property
    def is_draft(self):
        return False if self.publish else True


class Post(BasePost):
    """
    A default ``Post`` Class implementation.
    """
    pass
