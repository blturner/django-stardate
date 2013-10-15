from django.conf.urls import patterns, url

from stardate.feeds import LatestPostsFeed
from stardate import views


urlpatterns = patterns('',
    url(r'^$', views.PostArchiveIndex.as_view(), name='post-archive-index'),
    url(r'rss/$', LatestPostsFeed(), name='post-feed'),
    url(r'^(?P<year>\d{4})/$', views.PostYearArchive.as_view(), name='post-archive-year'),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/$', views.PostMonthArchive.as_view(), name='post-archive-month'),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/$', views.PostDayArchive.as_view(), name='post-archive-day'),
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/(?P<post_slug>[-\w]+)/$',
        views.PostDetail.as_view(), name='post-detail'),
    url(r'^(?P<post_slug>[-\w]+)/edit/$', views.PostEdit.as_view(), name='post-edit')
)
