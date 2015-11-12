from django.db import models

from stardate.models import BasePost


class CustomPost(BasePost):
    """
    A subclass of stardate.models.BasePost which adds an extra field.
    """
    extra_field = models.CharField(max_length=255)

    class Meta:
        app_label = 'core'
