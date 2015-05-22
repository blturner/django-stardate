from django.conf.urls import patterns, url

from stardate import views


urlpatterns = patterns('',
    url(r'^file_list/$', views.get_file_list, name='backend-file-list'),
)
