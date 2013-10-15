from django.db import models

from stardate.models import BasePost


class Post(BasePost):
    """
    A simple subclass of stardate.models.BasePost.
    """
    pass


class CustomPost(BasePost):
    """
    A subclass of stardate.models.BasePost which adds an extra field.
    """
    extra_field = models.CharField(max_length=255)
