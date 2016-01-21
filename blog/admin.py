from django.contrib import admin
from models import *


class GenecologyUserAdmin(admin.ModelAdmin):
    class Meta:
        model = GenecologyUser


class PostAdmin(admin.ModelAdmin):
    class Meta:
        model = Post

    exclude = ('slug', )
    list_display = ('title', 'created', 'creator', )


admin.site.register(GenecologyUser, GenecologyUserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Tag)
