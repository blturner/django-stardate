import tempfile

from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from social.apps.django_app.default.models import UserSocialAuth

from stardate.models import Blog
from stardate.utils import get_post_model

Post = get_post_model()


def create_user(**kwargs):
    defaults = {
        "username": "bturner",
    }
    defaults.update(kwargs)
    user, created = User.objects.get_or_create(**defaults)
    return user


def create_user_social_auth(**kwargs):
    defaults = {
        "provider": "dropbox",
        "uid": "1234",
        "user": kwargs['user'],
        "extra_data": {
            "access_token": {
                u'oauth_token_secret': u'oauth_token_secret_string',
                u'oauth_token': u'oauth_token_string',
                u'uid': u'123'
            }
        }
    }
    defaults.update(kwargs)
    social_auth, created = UserSocialAuth.objects.get_or_create(**defaults)
    return social_auth


def create_blog(**kwargs):
    backend_file, backend_file_path = tempfile.mkstemp(suffix='.txt')
    defaults = {
        "name": "Test blog",
        "backend_file": backend_file_path,
    }
    defaults['slug'] = slugify(defaults['name'])
    defaults.update(kwargs)

    if "user" not in defaults:
        defaults["user"] = create_user()

    defaults["social_auth"] = create_user_social_auth(
        user=defaults["user"])

    blog, created = Blog.objects.get_or_create(**defaults)
    return blog


def create_post(**kwargs):
    push = kwargs.pop('push', True)
    defaults = {
        "blog": kwargs['blog'],
        "body": "Test post body.",
        "title": "Test post title",
    }
    defaults.update(kwargs)
    defaults["slug"] = slugify(defaults["title"])
    post = Post(**defaults)
    post.save(push=push)
    return post
