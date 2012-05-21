from django.contrib import admin

from stardate.models import DropboxAuth, DropboxFile, DropboxFolder, Blog, Post


class DropboxAuthAdmin(admin.ModelAdmin):
    pass


class DropboxFileAdmin(admin.ModelAdmin):
    pass


class DropboxFolderAdmin(admin.ModelAdmin):
    pass


class BlogAdmin(admin.ModelAdmin):
    pass


class PostAdmin(admin.ModelAdmin):
    pass


admin.site.register(DropboxAuth, DropboxAuthAdmin)
admin.site.register(DropboxFile, DropboxFileAdmin)
admin.site.register(DropboxFolder, DropboxFolderAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
