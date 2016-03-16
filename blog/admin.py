from django.contrib import admin
from django import forms
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet, generic_inlineformset_factory
from django.contrib.contenttypes.admin import GenericTabularInline, GenericStackedInline
from django.core.exceptions import *

from reversion.admin import VersionAdmin

from models import *


def help_text(s):
    """
    Cleans up help strings so that we can write them in ways that are
    human-readable without screwing up formatting in the admin interface.
    """
    return re.sub('\s+', ' ', s).strip()


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
            'concept',
            'summary',
            'description',
            'commit_message'
        )

class ExternalResourceAdminForm(forms.ModelForm):
    commit_message = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = ExternalResource
        fields = (
            'about',
            'tags',
            'name',
            'resource_type',
            'source',
            'source_location',
            'identifier',
            'identifier_type',
            'description',
            'commit_message'
        )


class ImageAdminForm(forms.ModelForm):
    commit_message = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Image
        fields = (
            'about',
            'tags',
            'name',
            'source',
            'source_location',
            'identifier',
            'identifier_type',
            'image',
            'remote',
            'original_format',
            'description',
            'commit_message'
        )


class DataAdminForm(forms.ModelForm):
    commit_message = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Data
        fields = (
            'about',
            'tags',
            'instance_of',
            'name',
            'source',
            'source_location',
            'identifier',
            'identifier_type',
            'data_format',
            'location',
            'description',
            'commit_message'
        )


class PropertyAdminForm(forms.ModelForm):

    class Meta:
        model = Property
        fields = (
            'concept',
            'instance_of',
            'source',
            'target',
        )

    def clean(self):
        """
        Ensure that the source and target :class:`.Entity` instances are in the
        domain and range of the selected :class:`.RDFProperty`\.
        """
        super(PropertyAdminForm, self).clean()
        data = self.cleaned_data
        if not data['source'].is_a(data['instance_of'].domain):
            raise ValidationError(help_text("""
                Cannot apply this type of property to the selected entities:
                source entity is not in the domain of the selected property
                type. Choose a %s as source, or select a different property
                type.""" % data['instance_of'].domain.__unicode__()))

        if not data['target'].is_a(data['instance_of'].range):
            raise ValidationError(help_text("""
                Cannot apply this type of property to the selected entities:
                target entity is not in the range of the selected property
                type. Choose a %s as target, or select a different property
                type.""" % data['instance_of'].range.__unicode__()))


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


class NoteAdmin(admin.ModelAdmin):
    class Meta:
        model = Note
    # form = PostAdminForm

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


class DataAdmin(admin.ModelAdmin):
    class Meta:
        model = Data

    form = DataAdminForm
    raw_id_fields = ('tags', 'about',)
    autocomplete_lookup_fields = {
        'm2m': ['tags', 'about'],
    }

    list_display = ('name', 'data_format', 'creator', 'created', 'updated')

    def save_model(self, request, obj, form, change):
        """
        Set the current user as creator.
        """
        try:
            obj.creator
        except:
            obj.creator = request.user
        obj.save()


class ConceptProfileAdmin(admin.ModelAdmin):
    class Meta:
        model = ConceptProfile

    form = ConceptProfileAdminForm
    list_display = ('concept', 'creator', 'created', 'updated')
    search_fields = ('concept__label',)
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


class ImageAdmin(VersionAdmin, admin.ModelAdmin):
    class Meta:
        model = Image
    raw_id_fields = ('tags', 'about',)
    exclude = ('slug', )
    list_display = ('name', 'created', 'updated', 'creator', )
    autocomplete_lookup_fields = {
        'm2m': ['tags', 'about'],
    }
    form = ImageAdminForm
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


class ExternalResourceAdmin(VersionAdmin, admin.ModelAdmin):
    class Meta:
        model = ExternalResource

    raw_id_fields = ('tags', 'about',)
    exclude = ('slug', )
    list_display = ('name', 'resource_type', 'created', 'updated', 'creator', )
    autocomplete_lookup_fields = {
        'm2m': ['tags', 'about'],
    }
    form = ExternalResourceAdminForm
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


class RDFPropertyAdmin(admin.ModelAdmin):
    class Meta:
        model = RDFProperty

    exclude = []
    list_display = ['label', 'identifier', 'domain', 'range', 'partOf']
    list_filter = ['partOf', 'domain', 'range']
    search_fields = ['label', 'identifier']


class RDFClassAdmin(admin.ModelAdmin):
    class Meta:
        model = RDFClass

    exclude = []
    search_fields = ['label', 'identifier']
    list_display = ['identifier', 'label', 'comment']


class EntityAdmin(admin.ModelAdmin):
    class Meta:
        model = Entity

    # form = ConceptProfileAdminForm
    raw_id_fields = ('instance_of', 'concept')
    exclude = []
    list_display = ['label', 'instance_of', 'concept']

    def save_model(self, request, obj, form, change):
        """
        Set the current user as creator.
        """
        try:
            obj.creator
        except:
            obj.creator = request.user
        obj.save()


class PropertyAdmin(admin.ModelAdmin):
    class Meta:
        model = Property
    form = PropertyAdminForm

    # form = ConceptProfileAdminForm
    raw_id_fields = ('source', 'target', 'instance_of', 'concept')
    exclude = []
    list_display = ('instance_of', 'source', 'target',)
    autocomplete_lookup_fields = {
        'fk': ['source', 'target',],
    }

    def save_model(self, request, obj, form, change):
        """
        Set the current user as creator.
        """
        try:
            obj.creator
        except:
            obj.creator = request.user
        obj.save()


class EntityInline(admin.TabularInline):
    model = Entity





admin.site.register(GenecologyUser, GenecologyUserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ContentRelation, ContentRelationAdmin)
admin.site.register(ConceptProfile, ConceptProfileAdmin)
admin.site.register(Data, DataAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(ExternalResource, ExternalResourceAdmin)

admin.site.register(RDFSchema)
admin.site.register(RDFClass, RDFClassAdmin)
admin.site.register(RDFProperty, RDFPropertyAdmin)

admin.site.register(Entity, EntityAdmin)
admin.site.register(Property, PropertyAdmin)
