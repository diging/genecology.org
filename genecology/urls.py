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


from blog import views as blog_views
from blog import api



urlpatterns = [
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^logout/$', blog_views.logout_view, name='logout'),
    url(r'^$', blog_views.home, name='home'),
    url(r'^about/$', blog_views.about, name='about'),
    url(r'^blog/$', blog_views.blog, name='blog'),
    url(r'^notes/$', blog_views.notes, name='notes'),
    url(r'^topic/$', blog_views.topics, name='topics'),
    url(r'^contribute/$', blog_views.contribute, name='contribute'),
    url(r'^methods/$', blog_views.methods, name='methods'),
    url(r'^team/$', blog_views.team, name='team'),
    url(r'^concepts/(?P<profile_id>[0-9]+)/$', blog_views.conceptprofile, name='conceptprofile'),
    url(r'^concepts/people/$', blog_views.people, name='people'),
    url(r'^concepts/people/(?P<profile_id>[0-9]+)/$', blog_views.conceptprofile, name='person'),
    url(r'^concepts/people[/]?.json$', api.PeopleListView.as_view(), name='people_rest_list'),
    url(r'^concepts/places/$', blog_views.places, name='places'),
    url(r'^concepts/places[/]?.json$', api.PlaceListView.as_view(), name='places_rest_list'),
    url(r'^concepts/institutions/$', blog_views.institutions, name='institutions'),
    url(r'^concepts/institutions[/]?.json$', api.InstitutionListView.as_view(), name='institutions_rest_list'),
    url(r'^concepts/organisms/$', blog_views.organisms, name='organisms'),
    url(r'^concepts/organisms[/]?.json$', api.OrganismListView.as_view(), name='organisms_rest_list'),
    url(r'^post/(?P<post_id>[0-9]+)/$', blog_views.post, name='post'),
    url(r'^note/(?P<note_id>[0-9]+)/$', blog_views.note, name='note'),
    url(r'^data/(?P<data_id>[0-9]+)/$', blog_views.datum, name='datum'),
    url(r'^post/(?P<post_id>[0-9]+)[/]?.json$', blog_views.post_rest_detail, name='post_rest_detail'),
    url(r'^topic/(?P<tag_id>[0-9]+)/$', blog_views.tag, name='tag'),
    url(r'^topic/(?P<tag_id>[0-9]+)[/]?.json$', blog_views.tag_rest_detail, name='tag_rest_detail'),
    url(r'^search/', blog_views.PostSearchView.as_view(), name='search'),
    url(r'^admin/', admin.site.urls),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^evernote/note/(?P<note_id>[a-zA-Z0-9\-]+)$', blog_views.evernote_preview_note, name='evernote-preview-note'),
    url(r'^evernote/note/(?P<note_id>[a-zA-Z0-9\-]+)/sync/$', blog_views.evernote_sync_note, name='evernote-sync-note'),
    url(r'^evernote/notebooks/$', blog_views.evernote_list_notebooks, name='evernote-list-notebooks'),
    url(r'^evernote/notebooks/(?P<notebook_id>[a-zA-Z0-9\-]+)/$', blog_views.evernote_list_notes, name='evernote-list-notes')
]
