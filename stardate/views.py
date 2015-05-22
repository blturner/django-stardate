import json

from django.conf import settings
from django.db.models.loading import get_model
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views import generic

from stardate.backends.dropbox import DropboxBackend
from stardate.models import Blog
from stardate.utils import get_post_model

Post = get_post_model()


class PostViewMixin(object):
    model = Post
    date_field = 'publish'

    def get_queryset(self):
        blog = get_object_or_404(Blog, slug__iexact=self.kwargs['blog_slug'])
        return Post.objects.published().filter(blog=blog)


class PostArchiveIndex(PostViewMixin, generic.ArchiveIndexView):
    context_object_name = 'post_list'

    def get_context_data(self, **kwargs):
        context = super(PostArchiveIndex, self).get_context_data(**kwargs)
        context['blog'] = Blog.objects.get(slug__iexact=self.kwargs['blog_slug'])
        return context


class PostYearArchive(PostViewMixin, generic.YearArchiveView):
    make_object_list = True


class PostMonthArchive(PostViewMixin, generic.MonthArchiveView):
    pass


class PostDayArchive(PostViewMixin, generic.DayArchiveView):
    pass


class PostDetail(PostViewMixin, generic.DateDetailView):
    context_object_name = 'post'
    slug_url_kwarg = 'post_slug'


class PostEdit(PostViewMixin, generic.UpdateView):
    context_object_name = 'post'
    slug_url_kwarg = 'post_slug'


def get_file_list(request):
    if not request.user.is_authenticated():
        raise Http404

    user = request.user
    # backend = user.social_auth.all()[0].provider
    backend = DropboxBackend()
    backend.set_social_auth(user.social_auth.all()[0])

    files = []
    source_list = backend.get_source_list()

    for source in source_list:
        files.append({'name': source[1]})

    return HttpResponse(json.dumps(files), content_type='application/json')
