from django.shortcuts import get_object_or_404
from django.views import generic

from stardate.models import Blog, Post


class PostViewMixin(object):
    model = Post
    date_field = 'publish'

    def get_queryset(self):
        blog = get_object_or_404(Blog, slug__iexact=self.kwargs['blog_slug'])
        return Post.objects.published().filter(blog=blog)


class PostArchiveIndex(PostViewMixin, generic.ArchiveIndexView):
    context_object_name = 'post_list'


class PostYearArchive(PostViewMixin, generic.YearArchiveView):
    make_object_list = True


class PostMonthArchive(PostViewMixin, generic.MonthArchiveView):
    pass


class PostDayArchive(PostViewMixin, generic.DayArchiveView):
    pass


class PostDetail(PostViewMixin, generic.DateDetailView):
    context_object_name = 'post'
    slug_url_kwarg = 'post_slug'
