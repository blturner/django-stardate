from django.contrib import admin

from stardate.models import DropboxFile, Blog, Post


class DropboxFileAdmin(admin.ModelAdmin):
    pass


class BlogAdmin(admin.ModelAdmin):
    pass


class PostAdmin(admin.ModelAdmin):
    pass


admin.site.register(DropboxFile, DropboxFileAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
