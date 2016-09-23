from django.shortcuts import render, get_object_or_404
from django import forms
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth import logout

from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import mixins
from rest_framework import generics

from haystack.generic_views import SearchView
from haystack.query import EmptySearchQuerySet, SearchQuerySet
from haystack.forms import SearchForm

from reversion.helpers import generate_patch_html

from models import *
from blog.serializers import *
from concepts.authorities import get_namespace, get_by_namespace

import urllib2 as urllib
import csv
import datetime

from blog import evernote_api, tasks


## Helper functions start here.

def validate_url(value):
    """
    Evaluate whether a string is a URL.
    """
    try:
        URLValidator()(value)
        return True
    except ValidationError:
        return False


def detect_uri(cell):
    """
    Convert URIs to labeled links to :class:`.ConceptProfile` view.

    Will create new :class:`.Concept` and :class:`.ConceptProfile` instances
    if a matching authority is found.
    """
    if validate_url(cell):
        namespace = get_namespace(cell)
        managers = get_by_namespace(namespace)
        if len(managers) > 0:
            concept = Concept.objects.get_or_create(uri=cell, authority=managers[0].__name__)[0]
            conceptprofile = ConceptProfile.objects.get_or_create(concept=concept, defaults={'creator_id': 1, 'summary': 'Pending', 'description': 'Pending'})[0]
            cpurl = reverse('conceptprofile', args=(conceptprofile.id,))
            cell = mark_safe('<a class="label label-success" href="%s">%s</a>' % (cpurl, concept.label))
    return cell


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
    return {'form': PostSearchForm}


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
        'active': 'home',
        'image': Image.objects.order_by('?').filter(feature=True).first()
    })
    return render(request, 'home.html', context)


def blog(request):
    context = get_default_context()
    context.update({
        'posts': Post.objects.filter(published=True).order_by('-created'),
        'tags': Tag.objects.all(),
        'active': 'blog',
    })
    return render(request, 'blog.html', context)


def notes(request):
    context = get_default_context()
    context.update({
        'notes': Note.objects.all().order_by('-created'),
        'tags': Tag.objects.all(),
        'active': 'notes',
    })
    return render(request, 'notes.html', context)


def topics(request):
    context = get_default_context()
    context.update({
        'tags': Tag.objects.all(),
        'active': 'topics',
    })
    return render(request, 'tags.html', context)


def datum(request, data_id):
    data_object = get_object_or_404(Data, pk=data_id)
    response = urllib.urlopen(data_object.location)
    reader = csv.reader(response)

    content = [[detect_uri(cell) for cell in row] for row in reader]

    context = get_default_context()
    context.update({
        'column_headers': content[0],
        'data': enumerate(content[1:]),
        'data_object': data_object,
    })
    return render(request, 'csv.html', context)


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


def note(request, note_id):
    """
    Display the content of a :class:`.Post`\.
    """


    note = get_object_or_404(Note, pk=note_id)

    about_relations = note.relations_from.filter(instance_of__identifier='P129_is_about')
    source_url = None
    if about_relations.count() > 0:
        for relation in about_relations:
            if hasattr(relation.target, 'resource_type') and relation.target.resource_type == ExternalResource.WEBSITE:
                source_url = relation.target.source_location

    available_versions = reversion.get_for_object(note)
    versions = get_version_data(available_versions)

    date, body, subtitle = available_versions[0].revision.date_created, note.content, None
    version_id = request.GET.get('version', None)

    if version_id and int(version_id) != available_versions[0].revision_id:
        version = available_versions.get(revision_id=version_id)
        note = version.object_version.object
        date = version.revision.date_created
        subtitle = 'Historical version %s' % version_id
        body = mark_safe(generate_patch_html(version, available_versions[0], 'content'))

    if not (request.user.is_staff or post.published):
        return HttpResponseNotFound("<h1>Note not found.</h1>")

    context = get_default_context()
    context.update({
        'note': note,
        'subtitle': subtitle,
        'date': date,
        'active': 'notes',
        'versions': versions,
        'type': 'note',
        'title': note.title,
        'body': body,
        'source_url': source_url
    })
    return render(request, 'note.html', context)


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
        'active': 'topics',
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
    profile = get_object_or_404(ConceptProfile, pk=profile_id)

    available_versions = reversion.get_for_object(profile)
    versions = get_version_data(available_versions)
    version_id = request.GET.get('version', None)
    body = profile.description
    subtitle = None

    conceptType = ContentType.objects.get_for_model(Concept)

    relations_to = ContentRelation.objects.filter(target_content_type_id=conceptType.id, target_instance_id=profile.concept.id)
    relations_from = ContentRelation.objects.filter(source_content_type_id=conceptType.id, source_instance_id=profile.concept.id)

    if version_id and int(version_id) != available_versions[0].revision_id:
        version = available_versions.get(revision_id=version_id)
        profile = version.object_version.object
        subtitle = 'Historical version %s' % version_id
        body = mark_safe(generate_patch_html(version, available_versions[0], 'description'))

    context = get_default_context()
    context.update({
        'profile': profile,
        'body': body,
        'active': '',
        'versions': versions,
        'subtitle': subtitle,
        'relations_from': relations_from,
        'relations_to': relations_to
    })
    return render(request, 'conceptprofile.html', context)


def conceptprofiles(request, queryset, typed='', body=''):
    context = get_default_context()
    context.update({
        'profiles': queryset,
        'title': typed.title(),
        'subtitle': None,
        'body': body,
        'active': 'profiles',
        'type': typed,
    })
    return render(request, 'conceptprofiles.html', context)


def people(request):
    """
    Lists :class:`blog.ConceptProfile`\s for :class:`concepts.Concept`\s with
    :class:`concepts.Type` E21 Person.
    """
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Person'])
    body = help_text("""
        Use the search interface below to find profiles about significant people
        in the history of evolutionary ecology. Profiles are automatically
        generated for people as we generate content related to them (e.g. blog
        posts, notes). As we learn more about these people, we will add
        biographical descriptions. If you know something about one of the people
        in this system, please let us know!""")
    return conceptprofiles(request, queryset, 'people', body)


def institutions(request):
    """
    """
    body = help_text("""
        Use the search interface below to find profiles about institutions
        related to the history of evolutionary ecology. Profiles are
        automatically generated for institutions as we generate content related
        to them (e.g. blog posts, notes). As we learn more about these
        institutions, we will add additional descriptions. If you know something
        about one of the institutions in this system, please let us know!""")
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Institution'])
    return conceptprofiles(request, queryset, 'institutions', body)


def organisms(request):
    body = help_text("""
        Use the search interface below to find profiles about organisms
        related to the history of evolutionary ecology. Profiles are
        automatically generated for organisms as we generate content related
        to them (e.g. blog posts, notes). As we learn more about these
        organisms, we will add additional descriptions. If you know something
        about one of the organims in this system, please let us know!""")
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Organism'])
    return conceptprofiles(request, queryset, 'organisms', body)


def places(request):
    body = help_text("""
        Use the search interface below to find profiles about places
        related to the history of evolutionary ecology. Profiles are
        automatically generated for places as we generate content related
        to them (e.g. blog posts, notes). As we learn more about these
        places, we will add additional descriptions. If you know something
        about one of the places in this system, please let us know!""")
    queryset = ConceptProfile.objects.filter(concept__typed__uri=settings.CONCEPT_TYPES['Place'])
    return conceptprofiles(request, queryset, 'places', body)


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


class PostSearchForm(SearchForm):
    """
    Form for searching blog :class:`.Post`\s.
    """
    q = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))



class PostSearchView(SearchView):
    """
    Provides the blog :class:`.Post` search views.
    """
    queryset = SearchQuerySet()
    results_per_page = 20
    form_class = PostSearchForm
    template_name = "search/search.html"

    # facet_fields = ('creator', 'created', 'type')

    def get_queryset(self):
        return super(PostSearchView, self).get_queryset()

    def get_context_data(self, *args, **kwargs):
        return super(PostSearchView, self).get_context_data(*args, **kwargs)


@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(request.GET.get('next', reverse('home')))



@staff_member_required
def evernote_list_notebooks(request):
    try:
        context = {
            'notebooks': evernote_api.list_notebooks(request.user)
        }
    except ObjectDoesNotExist:
        # TODO: generate an informative error page.
        return HttpResponseRedirect(reverse('home'))
    return render(request, 'evernote/list_notebooks.html', context)


@staff_member_required
def evernote_list_notes(request, notebook_id):
    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 20))
    try:
        context = {
            'notes': evernote_api.list_notes(request.user, notebook_id, offset=offset, max_notes=limit),
            'offset': offset,
            'limit': limit,
            'notebook_id': notebook_id,
            'previous_offset': offset - limit,
            'next_offset': offset + limit,
        }
    except ObjectDoesNotExist:
        # TODO: generate an informative error page.
        return HttpResponseRedirect(reverse('home'))
    return render(request, 'evernote/list_notes.html', context)


@staff_member_required
def evernote_sync_note(request, note_id):
    try:
        tasks.sync_note.delay(request.user.id, note_id)
    except Exception as E:
        # TODO: implement exception handling.
        raise
    last = request.GET.get('last', '/')
    return HttpResponseRedirect(last)


@staff_member_required
def evernote_preview_note(request, note_id):
    # try:
    context = {
        'note': evernote_api.get_note(request.user, note_id)
    }
    # except:
    #     # TODO: generate an informative error page.
    #     return HttpResponseRedirect(reverse('home'))
    return render(request, 'evernote/preview_note.html', context)
