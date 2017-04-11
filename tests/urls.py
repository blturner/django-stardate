from django.conf.urls import include, url

urlpatterns = [
    url(r'^social/', include('social_django.urls', namespace='social')),
    url(r'^', include('stardate.urls.index_urls')),
]
