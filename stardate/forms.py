from django import forms

from stardate.backends import get_backend
from stardate.models import Blog


backend = get_backend()


class BlogForm(forms.ModelForm):
    """
    A form that populates the backend file choices select field.
    """
    class Meta:
        model = Blog

    backend_file = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(BlogForm, self).__init__(*args, **kwargs)
        try:
            qs = Blog.objects.get(pk=self.instance.pk)
            backend.set_social_auth(qs.social_auth)
        except:
            pass

        self.fields['backend_file'].choices = backend.get_file_list()
