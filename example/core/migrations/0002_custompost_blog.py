# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stardate', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='custompost',
            name='blog',
            field=models.ForeignKey(related_name='core_custompost_related', to='stardate.Blog'),
        ),
    ]
