from __future__ import absolute_import

import requests

from blog.models import *
from blog import evernote_api

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from celery import shared_task

@shared_task
def sync_note(user_id, note_id):
    user = GenecologyUser.objects.get(pk=user_id)
    evernote_api.sync_note(user, note_id)
