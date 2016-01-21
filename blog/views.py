from django.shortcuts import render, get_object_or_404
from django import forms

from haystack.views import FacetedSearchView
from haystack.query import EmptySearchQuerySet
from haystack.forms import FacetedSearchForm

from models import *


class PostFacetedSearchForm(FacetedSearchForm):
    q = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))



def home(request):
    context = {
        'posts': Post.objects.all().order_by('-created'),
        'tags': Tag.objects.all(),
        'form': PostFacetedSearchForm,
    }
    return render(request, 'home.html', context)


def post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    context = {
        'post': post,
        'form': PostFacetedSearchForm,
    }
    return render(request, 'post.html', context)


def tag(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)

    context = {
        'tag': tag,
        'posts': tag.tagged_posts.all().order_by('-created'),
        'form': PostFacetedSearchForm,
    }
    return render(request, 'tag.html', context)


class PostSearchView(FacetedSearchView):
    pass
