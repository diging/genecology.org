from django.contrib import admin
from django.shortcuts import render, get_object_or_404
from django.conf.urls import url, include
from django import forms
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet, generic_inlineformset_factory
from django.contrib.contenttypes.admin import GenericTabularInline, GenericStackedInline
from django.core.exceptions import *

from reversion.admin import VersionAdmin

from models import *


def create_modeladmin(modeladmin, model, name = None):
    class  Meta:
        proxy = True
        app_label = model._meta.app_label

    attrs = {'__module__': '', 'Meta': Meta}

    newmodel = type(name, (model,), attrs)

    admin.site.register(newmodel, modeladmin)
    return modeladmin


def help_text(s):
    """
    Cleans up help strings so that we can write them in ways that are
    human-readable without screwing up formatting in the admin interface.
    """
    return re.sub('\s+', ' ', s).strip()


class SetCreatorMixin(object):
    def save_model(self, request, obj, form, change):
        """
        Set the current user as creator.
        """
        try:
            obj.creator
        except:
            obj.creator = request.user
        obj.save()


class TimeSpanPropertyForm(forms.ModelForm):
    instance_of = forms.ModelChoiceField(RDFProperty.objects.filter(domain__identifier='E52_Time-Span'), label='property type')
    value = forms.CharField(label='value', required=False,
                            widget=forms.SelectDateWidget(empty_label=("Choose Year", "Choose Month", "Choose Day"),
                                                          years=range(1800, 2016)))

    class Meta:
        model = Property
        fields = ('instance_of', )

    def save(self, *args, **kwargs):
        temporal_entity = self.cleaned_data['source']

        # E2 TEntity -[P4]-> E52 TSpan -[?]-> E61/dateTime.
        if not temporal_entity.time_span:
            timespan_instance = Entity(     # E52 instance.
                instance_of=RDFClass.objects.get(identifier='E52_Time-Span'),
                label='Time-span of %s' % temporal_entity.label,
            )
            timespan_instance.save()
            has_timespan = Property(        # P4 instance.
                instance_of=RDFProperty.objects.get(identifier='P4_has_time-span'),
                source=temporal_entity,
                target=timespan_instance
            )
            has_timespan.save()
        else:
            timespan_instance = temporal_entity.time_span

        target_class = self.cleaned_data['instance_of'].range

        # value is just a string, since we don't want to DateField validation to
        #  force the user to artificially inflate the precision of the date.
        year, month, day = self.cleaned_data['value'].split('-')
        if month == '0':
            precision = 'precision: year',
        elif day == '0':
            precision = 'precision: month',
        else:
            precision = 'precision: day'

        target_instance = Entity(
            instance_of=target_class,
            label=self.cleaned_data['value'],
        )
        target_instance.save()

        property_instance = Property(
            instance_of=self.cleaned_data['instance_of'],
            source=timespan_instance,
            target=target_instance,
        )

        property_instance.save()
        return property_instance


class TimeSpanInline(admin.TabularInline):
    model = Property
    fk_name = 'source'
    classes = ('grp-collapse grp-open',)
    form = TimeSpanPropertyForm
    extra = 1


class EventAdminForm(forms.ModelForm):
    # Only allow descendants of E5 Event.
    instance_of = forms.ModelChoiceField(RDFClass.objects.get(identifier='E5_Event').children, label='Event type')

    class Meta:
        model = Entity
        fields = ('label', 'instance_of', )

    def save(self, *args, **kwargs):
        return super(EventAdminForm, self).save(*args, **kwargs)


class EventAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('label', 'instance_of')
        }),
        ('Time span', {
            'classes': ('placeholder', 'properties_from-group'),
            'fields': ()
        })
    )

    form = EventAdminForm

    def get_queryset(self, *args, **kwargs):
        queryset = super(EventAdmin, self).get_queryset(*args, **kwargs)
        return queryset.filter(instance_of__in=RDFClass.objects.get(identifier='E5_Event').children)

    # def save_model(self, request, obj, form, change):
    #



    inlines = [TimeSpanInline,]


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
            'created',
            'published',
            'summary',
            'body',
            'commit_message'
        )


class NoteAdminForm(forms.ModelForm):
    commit_message = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Note
        fields = (
            'about',
            'tags',
            'title',
            'created',
            'content',
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
            'created_original',
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


class NoteAdmin(SetCreatorMixin, admin.ModelAdmin):
    class Meta:
        model = Note
    form = NoteAdminForm

    raw_id_fields = ('tags', 'about',)
    exclude = ('slug', )
    list_display = ('title', 'created', 'creator', )
    autocomplete_lookup_fields = {
        'm2m': ['tags', 'about'],
    }

    inlines = [ContentRelationInline]


class PostAdmin(SetCreatorMixin, admin.ModelAdmin):
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


class ContentRelationAdmin(admin.ModelAdmin):
    class Meta:
        model = ContentRelation
    form = ContentRelationAdminForm

    related_lookup_fields = {
        'generic': [['source_content_type', 'source_instance_id'],
                    ['target_content_type', 'target_instance_id']],
    }


class DataAdmin(SetCreatorMixin, admin.ModelAdmin):
    class Meta:
        model = Data

    form = DataAdminForm
    raw_id_fields = ('tags', 'about',)
    autocomplete_lookup_fields = {
        'm2m': ['tags', 'about'],
    }

    list_display = ('name', 'data_format', 'creator', 'created', 'updated')


class ConceptProfileAdmin(SetCreatorMixin, admin.ModelAdmin):
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


class TagAdmin(SetCreatorMixin, VersionAdmin, admin.ModelAdmin):
    class Meta:
        model = Tag

    form = TagAdminForm

    def log_change(self, request, object, message):
        comment = request.POST.get('commit_message', None)
        if comment:
            message = comment
        self.revision_context_manager.set_comment(message)
        super(VersionAdmin, self).log_change(request, object, message)


class ImageAdmin(SetCreatorMixin, VersionAdmin, admin.ModelAdmin):
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


class ExternalResourceAdmin(SetCreatorMixin, VersionAdmin, admin.ModelAdmin):
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


class EntityCreateRelationForm(forms.Form):
    relation_type = forms.ModelChoiceField(queryset=RDFProperty.objects.all())
    evidence = forms.ModelChoiceField(queryset=ExternalResource.objects.all())

class EntityCreateRelationSelectTargetForm(forms.Form):
    target = forms.ModelChoiceField(queryset=Entity.objects.all())


class EntityAdmin(SetCreatorMixin, admin.ModelAdmin):
    class Meta:
        model = Entity

    # form = ConceptProfileAdminForm
    raw_id_fields = ('instance_of', 'concept')
    exclude = []
    list_display = ['label', 'instance_of', 'concept']

    def create_relation(self, request, entity_id):
        """
        Prompt user to select a property type. Once selected, direct user to
        ``create_relation_target`` view.
        """

        entity = get_object_or_404(Entity, pk=entity_id)

        if request.method == 'POST':
            form = EntityCreateRelationForm(request.POST)
            if form.is_valid():
                params = [
                    request,
                    entity_id,
                    form.cleaned_data['relation_type'].id,
                    form.cleaned_data['evidence'].id
                ]
                request.method = 'GET'
                return self.create_relation_select_target(*params)

        form = EntityCreateRelationForm()
        form.fields['relation_type'].queryset = entity.instance_of.available_properties
        return render(request, 'entityform.html', {'form': form})

    def create_relation_select_target(self, request, entity_id, property_id, evidence_id):
        entity = get_object_or_404(Entity, pk=entity_id)
        property_class = get_object_or_404(RDFProperty, pk=property_id)
        evidence_instance = get_object_or_404(ExternalResource, pk=evidence_id)
        if request.method == 'POST':
            if form.is_valid():
                return


        form = EntityCreateRelationSelectTargetForm()
        form.fields['target'].queryset = property_class.range.children_instances
        return render(request, 'entityform.html', {'form': form})


    def get_urls(self):
        urls = super(EntityAdmin, self).get_urls()
        extra_urls = [
            url(r'^create/relation/(?P<entity_id>[0-9]+)/$', self.admin_site.admin_view(self.create_relation), name="entity_create_relation"),
        ]
        return extra_urls + urls


class PropertyAdmin(SetCreatorMixin, admin.ModelAdmin):
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
create_modeladmin(EventAdmin, name='event', model=Entity)
