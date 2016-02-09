from django.shortcuts import render, get_object_or_404
from django import forms
from django.http import HttpResponse, HttpResponseNotFound

from haystack.views import FacetedSearchView
from haystack.query import EmptySearchQuerySet
from haystack.forms import FacetedSearchForm

from models import *


## Helper functions start here.


def get_default_context():
    """
    Generate context used in most/all views.
    """
    return {'form': PostFacetedSearchForm}


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

    if not (request.user.is_staff or post.published):
        return HttpResponseNotFound("<h1>Post not found.</h1>")

    context = get_default_context()
    context.update({
        'post': post,
        'active': 'blog',
    })
    return render(request, 'post.html', context)


def tag(request, tag_id):
    """
    Displays all of the :class:`.Post`\s associated with a specific
    :class:`.Tag`\.
    """
    tag = get_object_or_404(Tag, pk=tag_id)

    context = get_default_context()
    context.update({
        'tag': tag,
        'posts': tag.tagged_posts.filter(published=True).order_by('-created'),
        'active': 'blog',
    })
    return render(request, 'tag.html', context)


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
