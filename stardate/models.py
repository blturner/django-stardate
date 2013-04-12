from django.contrib.auth.models import User
from django.core import serializers
from django.db import models
from django.utils import timezone

from social_auth.models import UserSocialAuth

from stardate.backends import get_backend


class Blog(models.Model):
    authors = models.ManyToManyField(User, blank=True, null=True)
    backend_file = models.CharField(blank=True, max_length=255)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, related_name="+")
    slug = models.SlugField()
    social_auth = models.ForeignKey(UserSocialAuth)

    backend = get_backend()

    def __init__(self, *args, **kwargs):
        super(Blog, self).__init__(*args, **kwargs)
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
        # self.backend.do_sync(path, post_list)


class PostManager(models.Manager):

    def published(self):
        return self.get_query_set().filter(
            deleted=False,
            publish__lte=timezone.now()).order_by('-publish')


class Post(models.Model):
    authors = models.ManyToManyField(User, blank=True, null=True)
    blog = models.ForeignKey(Blog)
    body = models.TextField(blank=True)
    deleted = models.BooleanField()
    objects = PostManager()
    publish = models.DateTimeField(blank=True, null=True, unique=True)
    slug = models.SlugField()
    stardate = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    class Meta:
        ordering = ['-publish']
        unique_together = ('slug', 'blog')

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

    def mark_deleted(self):
        self.deleted = True
        return self

    # On save, a post should parse the dropbox blog file
    # and update the post that was changed.
    # FIXME
    def save(self, *args, **kwargs):
        self.clean()
        self.clean_fields()
        self.validate_unique()
        super(Post, self).save(*args, **kwargs)

        # Use a signal to trigger a backend sync

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
