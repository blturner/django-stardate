from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^social/', include('social_auth.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('stardate.urls.index_urls')),
)
