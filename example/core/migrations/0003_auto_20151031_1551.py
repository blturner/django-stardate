# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_custompost_blog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custompost',
            name='authors',
            field=models.ManyToManyField(related_name='core_custompost_related', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
