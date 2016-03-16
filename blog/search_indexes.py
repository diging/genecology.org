from django.core.urlresolvers import reverse

import datetime
from haystack import indexes
from models import *


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    creator = indexes.CharField(model_attr='creator')
    created = indexes.DateTimeField(model_attr='created')
    type = indexes.CharField()
    link = indexes.CharField()

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(published=True).filter(created__lte=datetime.datetime.now())

    def prepare_creator(self, obj):
        return obj.creator.full_name

    def prepare_type(self, obj):
        return 'Post'

    def prepare_link(self, obj):
        return reverse("post", args=(obj.id,))


class NoteIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    creator = indexes.CharField(model_attr='creator')
    created = indexes.DateTimeField(model_attr='created')
    type = indexes.CharField()
    link = indexes.CharField()

    def get_model(self):
        return Note

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(created__lte=datetime.datetime.now())

    def prepare_creator(self, obj):
        return obj.creator.full_name

    def prepare_type(self, obj):
        return 'Note'

    def prepare_link(self, obj):
        return reverse("note", args=(obj.id,))


class ConceptProfileIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='concept')
    creator = indexes.CharField(model_attr='creator')
    created = indexes.DateTimeField(model_attr='created')
    type = indexes.CharField()
    link = indexes.CharField()

    def get_model(self):
        return ConceptProfile

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(created__lte=datetime.datetime.now())

    def prepare_creator(self, obj):
        return obj.creator.full_name

    def prepare_title(self, obj):
        return obj.concept.label

    def prepare_type(self, obj):
        return 'Profile'

    def prepare_link(self, obj):
        return reverse("person", args=(obj.id,))
