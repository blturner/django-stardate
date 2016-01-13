from django.conf.urls import include, url
from django.views import generic

from stardate.models import Blog
from stardate.views import BlogCreate, select_backend


urlpatterns = [
    url(r'^create/$', BlogCreate.as_view(), name='blog-create'),
    url(r'^providers/$', select_backend, name='provider-select'),
    url(r'^(?P<blog_slug>[-\w]+)/', include('stardate.urls.blog_urls')),
    url(r'^$', generic.ListView.as_view(model=Blog), name='blog-list'),
]
