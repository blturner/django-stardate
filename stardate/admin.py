from django.contrib import admin

from stardate.models import DropboxFile, Blog, Post


class DropboxFileAdmin(admin.ModelAdmin):
    pass


class BlogAdmin(admin.ModelAdmin):
    exclude = ['owner', ]
    prepopulated_fields = {'slug': ('name',)}

    def save_model(self, request, obj, form, change):
        """When creating a new object, set the owner field.
        """
        if not change:
            obj.owner = request.user
        obj.save()


class PostAdmin(admin.ModelAdmin):
    date_hierarchy = 'publish'
    fields = ('blog', 'title', 'slug', 'body', 'publish', 'authors')
    list_display = ('title', 'publish', 'blog')
    list_filter = ('blog', 'publish',)
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(DropboxFile, DropboxFileAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
