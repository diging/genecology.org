import datetime
from haystack import indexes
from models import *


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    creator = indexes.CharField(model_attr='creator')
    created = indexes.DateTimeField(model_attr='created')

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(published=True).filter(created__lte=datetime.datetime.now())

    def prepare_creator(self, obj):
        return obj.creator.full_name
