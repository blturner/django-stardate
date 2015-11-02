# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import markupfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('default', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('backend_class', models.CharField(default=b'stardate.backends.dropbox.DropboxBackend', max_length=255, blank=True)),
                ('backend_file', models.CharField(max_length=255, blank=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True)),
                ('authors', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
                ('social_auth', models.ForeignKey(blank=True, to='default.UserSocialAuth', null=True)),
                ('user', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
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
                ('authors', models.ManyToManyField(related_name='stardate_post_related', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('blog', models.ForeignKey(related_name='stardate_post_related', to='stardate.Blog')),
            ],
            options={
                'ordering': ['-publish'],
                'abstract': False,
            },
        ),
    ]
