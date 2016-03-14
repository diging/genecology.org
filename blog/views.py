from django.shortcuts import render, get_object_or_404
from django import forms
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from django.utils.safestring import mark_safe

from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import mixins
from rest_framework import generics

from haystack.views import FacetedSearchView
from haystack.query import EmptySearchQuerySet
from haystack.forms import FacetedSearchForm

from reversion.helpers import generate_patch_html

from models import *
from blog.serializers import *


## Helper functions start here.

def get_user_or_none(pk):
    """
    Retrieve a :class:`.GenecologyUser` by ``pk``, or (quiety) return ``None``.
    """
    try:
        return GenecologyUser.objects.get(pk=pk)
    except GenecologyUser.DoesNotExist:
        return None


def get_default_context():
    """
    Generate context used in most/all views.
    """
    return {'form': PostFacetedSearchForm}


def get_version_data(available_versions):
    """
    Build template-ready version data for ``obj``, suitable for use with the
    ``history_modal.html`` template fragment.
    """
    return [{
        'id': version.revision_id,
        'date_created': version.revision.date_created,
        'user': get_user_or_none(version.revision.user_id),
        'comment': version.revision.comment,
    } for version in available_versions]


## Views start here.


def home(request):
    """
    The root page of the site. Displays recent blog posts.
    """
    context = get_default_context()
    context.update({
        'posts': Post.objects.filter(published=True).order_by('-created'),
        'tags': Tag.objects.all(),
        'active': 'blog',
    })
    return render(request, 'home.html', context)


def post(request, post_id):
    """
    Display the content of a :class:`.Post`\.
    """
    post = get_object_or_404(Post, pk=post_id)
    available_versions = reversion.get_for_object(post)
    versions = get_version_data(available_versions)

    date, body, subtitle = available_versions[0].revision.date_created, post.body, None
    version_id = request.GET.get('version', None)

    if version_id and int(version_id) != available_versions[0].revision_id:
        version = available_versions.get(revision_id=version_id)
        post = version.object_version.object
        date = version.revision.date_created
        subtitle = 'Historical version %s' % version_id
        body = mark_safe(generate_patch_html(version, available_versions[0], 'body'))

    if not (request.user.is_staff or post.published):
        return HttpResponseNotFound("<h1>Post not found.</h1>")

    context = get_default_context()
    context.update({
        'post': post,
        'subtitle': subtitle,
        'date': date,
        'active': 'blog',
        'versions': versions,
        'type': 'post',
        'title': post.title,
        'body': body,
    })
    return render(request, 'post.html', context)


def post_rest_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    serializer = PostDetailSerializer(post)
    json = JSONRenderer().render(serializer.data)
    return HttpResponse(json, content_type='application/json')


def tag(request, tag_id):
    """
    Displays all of the :class:`.Post`\s associated with a specific
    :class:`.Tag`\.
    """

    tag = get_object_or_404(Tag, pk=tag_id)

    available_versions = reversion.get_for_object(tag)
    versions = get_version_data(available_versions)

    date, body, subtitle = available_versions[0].revision.date_created, tag.description, None
    version_id = request.GET.get('version', None)

    if version_id and int(version_id) != available_versions[0].revision_id:
        version = available_versions.get(revision_id=version_id)
        post = version.object_version.object
        date = version.revision.date_created
        subtitle = 'Historical version %s' % version_id
        body = mark_safe(generate_patch_html(version, available_versions[0], 'description'))

    context = get_default_context()
    context.update({
        'tag': tag,
        'date': date,
        'title': tag.title,
        'type': 'tag',
        'posts': tag.post_set.filter(published=True).order_by('-created'),
        'active': 'blog',
        'versions': versions,
        'subtitle': subtitle,
        'body': body,
    })
    return render(request, 'tag.html', context)


def tag_rest_detail(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    serializer = TagSerializer(tag)
    json = JSONRenderer().render(serializer.data)
    return HttpResponse(json, content_type='application/json')



def conceptprofile(request, profile_id):
    return HttpResponse()


# def conceptprofile_rest_list(request):
#     typed = request.GET.get('type', None)
#     queryset = ConceptProfile.objects.all()
#     filter(concept__typed__uri=settings.CONCEPT_TYPES['Person'])
#

def conceptprofiles(request, queryset, typed=''):
    context = get_default_context()
    context.update({
        'profiles': queryset,
        'title': typed.title(),
        'subtitle': None,
        'body': 'Describe',
        'active': '',
        'type': typed,
    })
    return render(request, 'conceptprofile.html', context)


def people(request):
    """
    Lists :class:`blog.ConceptProfile`\s for :class:`concepts.Concept`\s with
    :class:`concepts.Type` E21 Person.
    """
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Person'])
    return conceptprofiles(request, queryset, 'people')


def institutions(request):
    """
    """
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Institution'])
    return conceptprofiles(request, queryset, 'institutions')


def organisms(request):
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Organism'])
    return conceptprofiles(request, queryset, 'organisms')


def places(request):
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Place'])
    return conceptprofiles(request, queryset, 'places')


def about(request):
    """
    Describes the purpose and content of the site.
    """
    context = get_default_context()
    context.update({
        'active': 'about',
    })
    return render(request, 'about.html', context)


def methods(request):
    """
    Describes the methods that we use in this project.
    """
    context = get_default_context()
    context.update({
        'active': 'methods',
    })
    return render(request, 'methods.html', context)


def contribute(request):
    """
    Describes how researchers can contribute to the project.
    """
    context = get_default_context()
    context.update({
        'active': 'contribute',
    })
    return render(request, 'contribute.html', context)


def team(request):
    """
    Describes who is involved in the project, and how.
    """
    context = get_default_context()
    context.update({
        'active': 'team',
    })
    return render(request, 'team.html', context)


## Search.


class PostFacetedSearchForm(FacetedSearchForm):
    """
    Form for searching blog :class:`.Post`\s.
    """
    q = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))


class PostSearchView(FacetedSearchView):
    """
    Provides the blog :class:`.Post` search views.
    """
    pass
