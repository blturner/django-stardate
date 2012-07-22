from django.conf.urls import include, patterns, url
from django.views import generic

from stardate.models import Blog


urlpatterns = patterns('',
    url(r'^(?P<blog_slug>[-\w]+)/', include('stardate.urls.blog_urls')),
    url(r'^$', generic.ListView.as_view(model=Blog), name='blog-list'),
)
