from django.shortcuts import get_object_or_404
from django.views import generic

from stardate.models import Blog, Post


class BlogPostListView(generic.ListView):
    context_object_name = 'post_list'

    def get_queryset(self):
        blog = get_object_or_404(Blog, slug__iexact=self.kwargs['slug'])
        return Post.objects.published().filter(blog=blog)
