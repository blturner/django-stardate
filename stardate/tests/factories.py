from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from social_auth.models import UserSocialAuth

from stardate.models import Blog, Post


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
        "extra_data": {"access_token": "oauth_token_secret=oauth_token_secret_string&oauth_token=oauth_token_string"}
    }
    defaults.update(kwargs)
    social_auth, created = UserSocialAuth.objects.get_or_create(**defaults)
    return social_auth


def create_blog(**kwargs):
    defaults = {
        "name": "Test blog",
        "backend_file": "test_backend_file.md",
    }
    defaults.update(kwargs)

    if "user" not in defaults:
        defaults["user"] = create_user()

    defaults["social_auth"] = create_user_social_auth(
        user=defaults["user"])

    blog, created = Blog.objects.get_or_create(**defaults)
    return blog


def create_post(**kwargs):
    defaults = {
        "blog": kwargs['blog'],
        "body": "Test post body.",
        "title": "Test post title",
    }
    defaults.update(kwargs)
    defaults["slug"] = slugify(defaults["title"])
    post, created = Post.objects.get_or_create(**defaults)
    return post
