from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views import generic

from social.apps.django_app.default.models import UserSocialAuth

from stardate import backends
from stardate.forms import BlogForm, PostForm
from stardate.models import Blog
from stardate.utils import get_post_model

Post = get_post_model()


@method_decorator(login_required, name='dispatch')
class BlogCreate(generic.edit.CreateView):
    form_class = BlogForm
    model = Blog

    def get_initial(self):
        provider = self.kwargs['provider']
        user = self.request.user

        try:
            social_auth = UserSocialAuth.objects.get(user=user, provider=provider)
        except:
            social_auth = None

        self.initial.update({
            'social_auth': social_auth,
            'user': user,
        })

        return self.initial

    def get_success_url(self):
        return reverse('post-archive-index', kwargs={'blog_slug': self.object.slug})


class PostViewMixin(object):
    allow_empty = True
    model = Post
    date_field = 'publish'

    def get_queryset(self):
        blog = Blog.objects.get(slug__iexact=self.kwargs['blog_slug'])
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


class DraftArchiveIndex(PostViewMixin, generic.ListView):
    template_name = 'stardate/draft_list.html'

    def get_queryset(self):
        blog = Blog.objects.get(slug__iexact=self.kwargs['blog_slug'])
        return Post.objects.drafts().filter(blog=blog)


class DraftPostDetail(PostViewMixin, generic.DetailView):
    template_name = 'stardate/draft_detail.html'

    def get_object(self):
        return Post.objects.get(
            blog__slug=self.kwargs['blog_slug'],
            stardate=self.kwargs['stardate']
        )


@method_decorator(login_required, name='dispatch')
class DraftEdit(PostViewMixin, generic.UpdateView):
    context_object_name = 'post'
    form_class = PostForm

    def get_object(self):
        return Post.objects.get(
            blog__slug=self.kwargs['blog_slug'],
            stardate=self.kwargs['stardate']
        )


@method_decorator(login_required, name='dispatch')
class PostCreate(PostViewMixin, generic.edit.CreateView):
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        blog = Blog.objects.get(slug=self.kwargs['blog_slug'])
        form.instance.blog = blog
        return super(PostCreate, self).form_valid(form)


@method_decorator(login_required, name='dispatch')
class PostEdit(PostViewMixin, generic.UpdateView):
    context_object_name = 'post'
    slug_url_kwarg = 'post_slug'
    form_class = PostForm


@login_required
def select_backend(request, **kwargs):
    if request.POST:
        backend = request.POST.get('backend')

        if backend == 'local':
            return HttpResponseRedirect(reverse('blog-create', kwargs={
                'provider': backend}))

        try:
            UserSocialAuth.objects.get(user=request.user, provider=backend)

            return HttpResponseRedirect(reverse('blog-create', kwargs={
                'provider': backend}))
        except UserSocialAuth.DoesNotExist:
            return HttpResponseRedirect(
                reverse('social:begin', kwargs={'backend': backend})
            )

    context = {
        'stardate_backends': backends.STARDATE_BACKENDS
    }

    return render_to_response(
        'stardate/providers.html',
        context,
        context_instance=RequestContext(request)
    )
