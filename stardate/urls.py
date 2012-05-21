from django.conf.urls import patterns, url

from stardate.views import read_dir, import_posts


urlpatterns = patterns('',
    url(r'^metadata/$', read_dir, name="dropbox-dir"),
    url(r'^import_posts/$', import_posts),
)
