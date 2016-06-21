import datetime
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core import serializers
from django.db import models
from django.db.models.query import QuerySet
from django.template.defaultfilters import slugify
from django.utils import timezone

from dateutil import tz
from markupfield.fields import MarkupField
from social.apps.django_app.default.models import UserSocialAuth

from stardate.utils import get_post_model

SERIALIZED_FIELDS = (
    'title',
    'publish',
    'stardate',
    'body',
    'timezone'
)


class Blog(models.Model):
    authors = models.ManyToManyField(User, blank=True)
    # Dot notation path to backend Class
    backend_class = models.CharField(max_length=255, blank=True)
    # Path to file or directory used by backend to determine
    # how and where to store / retrieve posts
    backend_file = models.CharField(blank=True, max_length=255)
    last_sync = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, related_name="+")
    slug = models.SlugField(unique=True)
    social_auth = models.ForeignKey(UserSocialAuth, blank=True, null=True)
    sync = models.BooleanField(default=True,
        help_text='This blog should sync using it\'s selected backend')


    def __unicode__(self):
        return self.name

    @property
    def backend(self):
        from stardate.backends import get_backend

        return get_backend(self.backend_class, blog=self)

    def clean(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('post-archive-index', (), {'blog_slug': self.slug})

    def get_backend_choice(self):
        choices = self.backend.get_source_list()
        return choices[int(self.backend_file)][1]

    @property
    def posts(self):
        """
        Dynamically looks up the related post model based on the model specified
        in the settings file and returns the related object queryset for that
        model.
        """
        POST_MODEL = getattr(settings, 'STARDATE_POST_MODEL')
        app_label, model_name = POST_MODEL.split('.')

        return getattr(self, '{}_{}_related'.format(app_label, model_name.lower()))

    def save(self, *args, **kwargs):
        self.clean()

        super(Blog, self).save(*args, **kwargs)


class PostManager(models.Manager):
    def drafts(self):
        """
        Returns all draft Post instances. A draft is considered to be a Post
        without a publish property.
        """
        try:
            queryset_method = self.get_queryset
        except AttributeError:
            queryset_method = self.get_query_set

        return queryset_method().filter(publish=None)

    def published(self):
        try:
            queryset_method = self.get_queryset
        except AttributeError:
            queryset_method = self.get_query_set

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
        # self.full_clean()
        self.clean()
        self.clean_fields()
        self.validate_unique()

        if not self.stardate:
            push = True

        if push and self.blog.sync:
            # Sync this post with our backend
            # need a serialized post here to pass in
            self.backend.push([self])
        super(BasePost, self).save(*args, **kwargs)

    def serialized(self):
        serialized = serializers.serialize('python', [self], fields=SERIALIZED_FIELDS)

        for s in serialized:
            if s['fields']['publish']:
                s['fields']['publish'] = datetime.datetime.strftime(
                    s['fields']['publish'].replace(tzinfo=tz.gettz(self.timezone)),
                    '%Y-%m-%d %I:%M %p %z'
                )

        return serialized[0]['fields']

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
        if not self.publish:
            return False
        next = self.blog.posts.filter(publish__gt=self.publish).exclude(
            id__exact=self.id).order_by('publish')
        if next:
            return next[0]
        return False

    def get_prev_post(self):
        if not self.publish:
            return False
        prev = self.blog.posts.filter(publish__lt=self.publish).exclude(
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
