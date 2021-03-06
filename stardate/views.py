import datetime
import logging
from hashlib import sha256
import hmac
import json
import threading

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
)
from django.shortcuts import get_object_or_404, render_to_response, render
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from social_django.models import UserSocialAuth

from stardate import backends
from stardate.forms import BackendForm, BlogForm, PostForm
from stardate.models import Blog
from stardate.utils import get_post_model

Post = get_post_model()
logger = logging.getLogger('stardate')


class BlogCreate(generic.edit.CreateView):
    form_class = BlogForm
    model = Blog

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(request, *args, **kwargs)

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
    slug_url_kwarg = 'post_slug'

    def get_queryset(self):
        blog = Blog.objects.get(slug__iexact=self.kwargs['blog_slug'])
        return blog.posts.published()


class DraftViewMixin(object):
    def get_queryset(self):
        return Post.objects.drafts().filter(blog__user=self.request.user)


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


class PostDateDetail(PostViewMixin, generic.DateDetailView):
    context_object_name = 'post'


class PostDetail(PostViewMixin, generic.DetailView):
    context_object_name = 'post'


class DraftArchiveIndex(PostViewMixin, generic.ListView):
    template_name = 'stardate/draft_list.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
       return super(self.__class__, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        blog = Blog.objects.get(
            slug__iexact=self.kwargs['blog_slug'], user=self.request.user)
        return Post.objects.drafts().filter(blog=blog)


class DraftPostDetail(DraftViewMixin, PostViewMixin, generic.DetailView):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
       return super(self.__class__, self).dispatch(request, *args, **kwargs)


class DraftEdit(DraftViewMixin, PostViewMixin, generic.UpdateView):
    context_object_name = 'post'
    form_class = PostForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
       return super(self.__class__, self).dispatch(request, *args, **kwargs)


class PostCreate(PostViewMixin, generic.edit.CreateView):
    model = Post
    form_class = PostForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
       return super(self.__class__, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        blog = Blog.objects.get(slug=self.kwargs['blog_slug'])
        form.instance.blog = blog
        return super(PostCreate, self).form_valid(form)


class PostEdit(PostViewMixin, generic.UpdateView):
    context_object_name = 'post'
    slug_url_kwarg = 'post_slug'
    form_class = PostForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
       return super(self.__class__, self).dispatch(request, *args, **kwargs)


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
        'form': BackendForm()
    }

    return render(request, 'stardate/providers.html', context)


@csrf_exempt
def process_webhook(request):
    if request.method == 'GET':
        challenge = request.GET.get('challenge')
        if not challenge:
            return HttpResponseForbidden()
        return HttpResponse(challenge)
    if not request.method == 'POST':
        raise Http404

    signature = request.META.get('HTTP_X_DROPBOX_SIGNATURE')
    if not signature:
        return HttpResponseForbidden()

    if not hmac.compare_digest(
        signature,
        hmac.new(settings.DROPBOX_APP_SECRET, request.body, sha256).hexdigest()):
        return HttpResponseForbidden()

    for user in json.loads(request.body.decode())['delta']['users']:
        threading.Thread(target=process_user, args=(user,)).start()
    return HttpResponse()

def process_user(user):
    logger.debug('processing: {}'.format(user))
    try:
        social_auth = UserSocialAuth.objects.get(uid=user)
        blogs = social_auth.user.blogs.all()

        logger.debug('found {} blog(s)'.format(len(blogs)))

        for blog in blogs:
            logger.info('processing {}'.format(blog.name))
            blog.backend.pull()
    except UserSocialAuth.DoesNotExist:
        logger.info('UserSocialAuth with uid {} not found.'.format(user))
