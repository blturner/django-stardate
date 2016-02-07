from django import forms
from django.utils.text import slugify

from markupfield.widgets import AdminMarkupTextareaWidget

from stardate import backends
from stardate.models import Blog
from stardate.utils import get_post_model


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
            'social_auth': forms.HiddenInput(),
            'user': forms.HiddenInput(),
        }

    def save(self):
        instance = super(BlogForm, self).save(commit=False)

        try:
            provider = instance.social_auth.provider
        except AttributeError:
            provider = 'local'

        instance.backend_class = backends.STARDATE_BACKENDS[provider]['module']

        if not instance.slug:
            instance.slug = slugify(instance.name)
        instance.save()

        return instance


class PostForm(forms.ModelForm):
    body = forms.CharField(widget=AdminMarkupTextareaWidget)

    class Meta:
        model = Post
        fields = [
            'title',
            'body',
            'publish',
            'timezone',
        ]
