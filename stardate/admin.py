from django.contrib import admin

from stardate.utils import get_post_model
from stardate.models import Blog
from stardate.forms import BlogForm, PostForm

Post = get_post_model()


class BlogAdmin(admin.ModelAdmin):
    fields = [
        'name',
        'slug',
        'backend_file',
        'user',
        'social_auth',
    ]
    prepopulated_fields = {'slug': ('name',)}


class PostAdmin(admin.ModelAdmin):
    date_hierarchy = 'publish'
    form = PostForm
    list_display = ('title', 'publish', 'blog')
    list_filter = ('blog', 'publish',)
    prepopulated_fields = {'slug': ('title',)}
    fields = [
        'blog',
        'title',
        'slug',
        'body',
        'publish',
        'timezone',
    ]


admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
