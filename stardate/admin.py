from django.contrib import admin

from stardate.models import DropboxFile, Blog, Post


class DropboxFileAdmin(admin.ModelAdmin):
    pass


class BlogAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


class PostAdmin(admin.ModelAdmin):
    fields = ('blog', 'title', 'slug', 'body', 'publish', 'authors')
    list_display = ('title', 'publish', 'blog')
    list_filter = ('blog', 'publish',)
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(DropboxFile, DropboxFileAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
