from django.contrib import admin

from stardate.models import Blog, Post
from stardate.forms import BlogForm


class BlogAdmin(admin.ModelAdmin):
    exclude = ['owner', ]
    fields = ('social_auth', 'backend_file', 'name', 'slug', 'authors')
    form = BlogForm
    prepopulated_fields = {'slug': ('name',)}

    def save_model(self, request, obj, form, change):
        """When creating a new object, set the owner field.
        """
        if not change:
            obj.owner = request.user
        obj.save()


class PostAdmin(admin.ModelAdmin):
    date_hierarchy = 'publish'
    fields = ('blog', 'title', 'slug', 'deleted', 'body', 'publish', 'authors')
    list_display = ('title', 'publish', 'blog', 'deleted')
    list_filter = ('blog', 'publish',)
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
