from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from markdown import markdown

from stardate.models import Blog
from stardate.utils import get_post_model

Post = get_post_model()


class LatestPostsFeed(Feed):
    def get_object(self, request, blog_slug):
        return get_object_or_404(Blog, slug=blog_slug)

    def title(self, obj):
        return "%s: Recent posts" % obj.name

    def link(self, obj):
        return obj.get_absolute_url()

    def items(self, obj):
        return Post.objects.published().filter(blog=obj)[:5]

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.publish

    def item_description(self, item):
        return markdown(item.body)[:300]
