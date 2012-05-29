import markdown

from django.db import models


class DropboxCommon(models.Model):
    bytes = models.IntegerField(blank=True)
    icon = models.CharField(max_length=255)
    is_dir = models.BooleanField()
    modified = models.DateTimeField(blank=True, null=True)
    path = models.CharField(max_length=255)
    rev = models.CharField(max_length=255)
    revision = models.IntegerField(blank=True, null=True)
    root = models.CharField(max_length=255)
    size = models.CharField(max_length=255)
    thumb_exists = models.BooleanField()

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.path


class DropboxFolder(DropboxCommon):
    hash = models.CharField(max_length=255)
    folder = models.ForeignKey('self', blank=True, null=True)


class DropboxFile(DropboxCommon):
    client_mtime = models.DateTimeField(blank=True, null=True)
    content = models.TextField(blank=True)
    folder = models.ForeignKey(DropboxFolder, blank=True, null=True)
    mime_type = models.CharField(max_length=255)


class Blog(models.Model):
    title = models.CharField(blank=True, max_length=255)
    dropbox_file = models.ForeignKey(DropboxFile)

    def __unicode__(self):
        return self.title

    def __init__(self, *args, **kwargs):
        super(Blog, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        super(Blog, self).save(*args, **kwargs)
        # Parse the dropbox_file and save individual posts
        markdown.markdown(self.dropbox_file.content,
            extensions=['mypreprocessor(blog_id=%s)' % self.id])


class Post(models.Model):
    title = models.CharField(blank=True, max_length=255)
    content = models.TextField(blank=True)
    blog = models.ForeignKey(Blog)

    def __unicode__(self):
        return self.title

    # On save, a post should parse the dropbox blog file
    # and update the post that was changed.
    # def save(self):
    #     pass
