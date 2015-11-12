# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import markupfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomPost',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', markupfield.fields.MarkupField(rendered_field=True)),
                ('body_markup_type', models.CharField(default=b'markdown', max_length=30, choices=[(b'', b'--'), (b'html', 'HTML'), (b'plain', 'Plain'), (b'markdown', 'Markdown')])),
                ('created', models.DateTimeField(auto_now=True)),
                ('_body_rendered', models.TextField(editable=False)),
                ('deleted', models.BooleanField(default=False)),
                ('publish', models.DateTimeField(null=True, blank=True)),
                ('slug', models.SlugField(unique=True)),
                ('stardate', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('extra_field', models.CharField(max_length=255)),
                ('authors', models.ManyToManyField(related_name='core_custompost_related', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
        ),
    ]
