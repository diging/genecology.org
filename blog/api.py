from django.conf import settings

from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import mixins, generics, filters

import django_filters


from models import *
from blog.serializers import *


class ConceptProfileFilter(django_filters.FilterSet):
    class Meta:
        model = ConceptProfile
        fields = {'concept__label': ['exact', 'icontains'],}


class ConceptProfileListView(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     generics.GenericAPIView):
    pagination_class = PageNumberPagination
    serializer_class = ConceptProfileListSerializer
    queryset = ConceptProfile.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ConceptProfileFilter

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class PeopleListView(ConceptProfileListView):
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Person'])


class InstitutionListView(ConceptProfileListView):
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Institution'])


class OrganismListView(ConceptProfileListView):
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Organism'])


class PlaceListView(ConceptProfileListView):
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Place'])
