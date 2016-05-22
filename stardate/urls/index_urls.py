from django.conf.urls import include, url
from django.views import generic

from stardate.models import Blog
from stardate.views import (
    BlogCreate,
    select_backend,
    verify_dropbox_webhook,
    process_webhook
)


urlpatterns = [
    url(r'^new/$', select_backend, name='blog-new'),
    url(r'^create/(?P<provider>[-\w]+)/$', BlogCreate.as_view(), name='blog-create'),
    url(r'^providers/$', select_backend, name='provider-select'),
    url(r'^verify/$', verify_dropbox_webhook, name='verify'),
    url(r'^webook/$', process_webhook, name='webhook'),
    url(r'^(?P<blog_slug>[-\w]+)/', include('stardate.urls.blog_urls')),
    url(r'^$', generic.ListView.as_view(model=Blog), name='blog-list'),
]
