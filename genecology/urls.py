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

from blog import views as blog_views

sqs = SearchQuerySet().facet('creator', size=100)


urlpatterns = [
    url(r'^$', blog_views.home, name='home'),
    url(r'^about/$', blog_views.about, name='about'),
    url(r'^contribute/$', blog_views.contribute, name='contribute'),
    url(r'^methods/$', blog_views.methods, name='methods'),
    url(r'^team/$', blog_views.team, name='team'),
    url(r'^post/(?P<post_id>[0-9]+)/$', blog_views.post, name='post'),
    url(r'^tag/(?P<tag_id>[0-9]+)/$', blog_views.tag, name='tag'),
    url(r'^search/', blog_views.PostSearchView(form_class=blog_views.PostFacetedSearchForm, searchqueryset=sqs), name='search'),
    url(r'^admin/', admin.site.urls),
]
