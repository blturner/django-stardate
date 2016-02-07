# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-09 21:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import markupfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20151031_1551'),
    ]

    operations = [
        migrations.AddField(
            model_name='custompost',
            name='timezone',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='custompost',
            name='body',
            field=markupfield.fields.MarkupField(blank=True, rendered_field=True),
        ),
        migrations.AlterField(
            model_name='custompost',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]