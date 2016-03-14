from django.contrib import admin
from django import forms
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet, generic_inlineformset_factory
from django.contrib.contenttypes.admin import GenericTabularInline, GenericStackedInline

from reversion.admin import VersionAdmin

from models import *


class TagAdminForm(forms.ModelForm):
    commit_message = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Tag
        fields = ('slug', 'title', 'description', 'commit_message')


class ContentRelationAdminForm(forms.ModelForm):
    commit_message = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = ContentRelation
        fields = (
            'name',
            'description',
            'source_content_type',
            'source_instance_id',
            'target_content_type',
            'target_instance_id',
            'commit_message'
        )


class PostAdminForm(forms.ModelForm):
    commit_message = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Post
        fields = (
            'about',
            'tags',
            'title',
            'published',
            'summary',
            'body',
            'commit_message'
        )


class ConceptProfileAdminForm(forms.ModelForm):
    commit_message = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = ConceptProfile
        fields = (
            'tags',
            'slug',
            'concept',
            'summary',
            'description',
            'commit_message'
        )



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
    form = PostAdminForm

    raw_id_fields = ('tags', 'about',)
    exclude = ('slug', )
    list_display = ('title', 'created', 'creator', )
    autocomplete_lookup_fields = {
        'm2m': ['tags', 'about'],
    }

    inlines = [ContentRelationInline]

    def save_model(self, request, obj, form, change):
        """
        Set the current user as creator.
        """
        try:
            obj.creator
        except:
            obj.creator = request.user
        obj.save()


class ContentRelationAdmin(admin.ModelAdmin):
    class Meta:
        model = ContentRelation
    form = ContentRelationAdminForm

    related_lookup_fields = {
        'generic': [['source_content_type', 'source_instance_id'],
                    ['target_content_type', 'target_instance_id']],
    }


class ConceptProfileAdmin(admin.ModelAdmin):
    class Meta:
        model = ConceptProfile

    form = ConceptProfileAdminForm
    raw_id_fields = ('tags',)
    exclude = ('about', )
    raw_id_fields = ('concept',)
    autocomplete_lookup_fields = {
        'm2m': ['tags'],
        'fk': ['concept'],
    }
    inlines = [ContentRelationInline,]

    def save_model(self, request, obj, form, change):
        """
        Set the current user as creator.
        """
        try:
            obj.creator
        except:
            obj.creator = request.user
        obj.save()


class TagAdmin(VersionAdmin, admin.ModelAdmin):
    class Meta:
        model = Tag

    form = TagAdminForm

    def log_change(self, request, object, message):
        comment = request.POST.get('commit_message', None)
        if comment:
            message = comment
        self.revision_context_manager.set_comment(message)
        super(VersionAdmin, self).log_change(request, object, message)


admin.site.register(GenecologyUser, GenecologyUserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ContentRelation, ContentRelationAdmin)
admin.site.register(ConceptProfile, ConceptProfileAdmin)
