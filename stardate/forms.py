from django import forms
from django.utils.text import slugify

from markupfield.widgets import AdminMarkupTextareaWidget

from stardate.backends import get_backend
from stardate.models import Blog
from stardate.utils import get_post_model


backend = get_backend()
Post = get_post_model()


class BlogForm(forms.ModelForm):
    """
    A form that populates the backend file choices select field.
    """
    class Meta:
        model = Blog
        fields = [
            'name',
            'social_auth',
            'backend_file',
            'user',
        ]
        widgets = {
            'user': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super(BlogForm, self).__init__(*args, **kwargs)
        try:
            qs = Blog.objects.get(pk=self.instance.pk)
            backend.set_social_auth(qs.social_auth)
        except:
            pass

    def save(self):
        instance = super(BlogForm, self).save(commit=False)

        if not instance.slug:
            instance.slug = slugify(instance.name)
        instance.save()

        return instance


class PostForm(forms.ModelForm):
    body = forms.CharField(widget=AdminMarkupTextareaWidget)

    class Meta:
        model = Post
        fields = [
            'blog',
            'title',
            'slug',
            'body',
            'publish',
            'timezone',
            'authors',
        ]
