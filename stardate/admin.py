from django.contrib import admin

from stardate.utils import get_post_model
from stardate.models import Blog
from stardate.forms import BlogForm, PostForm

Post = get_post_model()


class BlogAdmin(admin.ModelAdmin):
    exclude = ['user', ]
    fields = ('social_auth', 'backend_file', 'name', 'slug', 'authors')
    form = BlogForm
    prepopulated_fields = {'slug': ('name',)}

    def save_model(self, request, obj, form, change):
        """
        When creating a new object, set the user field.
        """
        if not change:
            obj.user = request.user
        obj.save()


class PostAdmin(admin.ModelAdmin):
    date_hierarchy = 'publish'
    fields = ('blog', 'title', 'slug', 'body', 'publish', 'authors')
    form = PostForm
    list_display = ('title', 'publish', 'blog', 'deleted')
    list_filter = ('blog', 'publish',)
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
