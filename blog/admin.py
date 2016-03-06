from django.contrib import admin
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet, generic_inlineformset_factory
from django.contrib.contenttypes.admin import GenericTabularInline, GenericStackedInline

from models import *


class GenecologyUserAdmin(admin.ModelAdmin):
    class Meta:
        model = GenecologyUser


class ContentRelationInline(GenericTabularInline):
    model = ContentRelation
    extra = 0

    related_lookup_fields = {
        'generic': [['source_content_type', 'source_instance_id'],
                    ['target_content_type', 'target_instance_id']],
    }

    formset = generic_inlineformset_factory(ContentRelation,
                                            ct_field='source_content_type',
                                            fk_field='source_instance_id')

    ct_field = 'source_content_type'
    ct_fk_field = 'source_instance_id'


class PostAdmin(admin.ModelAdmin):
    class Meta:
        model = Post

    raw_id_fields = ('tags', 'about',)
    exclude = ('slug', )
    list_display = ('title', 'created', 'creator', )
    autocomplete_lookup_fields = {
        'm2m': ['tags', 'about'],
    }

    inlines = [ContentRelationInline]


class ContentRelationAdmin(admin.ModelAdmin):
    class Meta:
        model = ContentRelation

    related_lookup_fields = {
        'generic': [['source_content_type', 'source_instance_id'],
                    ['target_content_type', 'target_instance_id']],
    }


class ConceptProfileAdmin(admin.ModelAdmin):
    class Meta:
        model = ConceptProfile

    raw_id_fields = ('tags',)
    exclude = ('about', )
    raw_id_fields = ('concept',)
    autocomplete_lookup_fields = {
        'm2m': ['tags'],
        'fk': ['concept'],
    }
    inlines = [ContentRelationInline,]


admin.site.register(GenecologyUser, GenecologyUserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Tag)
admin.site.register(ContentRelation, ContentRelationAdmin)
admin.site.register(ConceptProfile, ConceptProfileAdmin)
