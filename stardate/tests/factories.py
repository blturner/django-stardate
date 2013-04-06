from django.contrib.auth.models import User

from social_auth.models import UserSocialAuth

from stardate.models import Blog, Post


def create_user(**kwargs):
    defaults = {
        "username": "bturner",
    }
    defaults.update(kwargs)
    return User.objects.create(
        **defaults)


def create_user_social_auth(**kwargs):
    defaults = {
        "provider": "dropbox",
        "uid": "1234",
        "user": kwargs['user'],
        "extra_data": {"access_token": "oauth_token_secret=oauth_token_secret_string&oauth_token=oauth_token_string"}
    }
    defaults.update(kwargs)
    return UserSocialAuth.objects.create(**defaults)


def create_blog(**kwargs):
    defaults = {
        "name": "Test blog",
        "backend_file": "0",
    }
    defaults.update(kwargs)

    if "owner" not in defaults:
        defaults["owner"] = create_user()

    defaults["social_auth"] = create_user_social_auth(
        user=defaults["owner"])

    return Blog.objects.create(
        **defaults)


def create_post(**kwargs):
    defaults = {
        "blog": kwargs['blog'],
        "body": "Test post body.",
        "title": "Test post title",
    }
    defaults.update(kwargs)
    return Post.objects.create(**defaults)
