# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('stardate', '0002_auto_20151031_1551'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='authors',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
