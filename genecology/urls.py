"""genecology URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin


from haystack.views import FacetedSearchView
from haystack.query import SearchQuerySet

from blog.views import PostSearchView, PostFacetedSearchForm

sqs = SearchQuerySet().facet('creator', size=100)


urlpatterns = [
    url(r'^$', 'blog.views.home', name='home'),
    url(r'^post/(?P<post_id>[0-9]+)/$', 'blog.views.post', name='post'),
    url(r'^tag/(?P<tag_id>[0-9]+)/$', 'blog.views.tag', name='tag'),
    url(r'^search/', PostSearchView(form_class=PostFacetedSearchForm, searchqueryset=sqs), name='search'),
    url(r'^admin/', admin.site.urls),
]
