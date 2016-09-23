from django.core.files.base import ContentFile, File
from django.conf import settings

from blog.models import *

from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.ttypes import NoteSortOrder

import datetime, os, pytz
from uuid import uuid4


EXTENSIONS = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/tiff': '.tiff',
    'application/pdf': '.pdf',
}


def _get_client(user):
    token = user.social_auth.get(provider='evernote').extra_data['oauth_token']
    client = EvernoteClient(token=token, sandbox=False)
    return client, token


def _get_note_store(user):
    client, token = _get_client(user)
    return client.get_note_store(), token


# EN timestamps are in mseconds.
_to_datetime = lambda i: datetime.datetime.fromtimestamp(i/1000, pytz.UTC)

def _get_external_notebook(guid):
    try:
        return ExternalNotebook.objects.get(external_id=guid)
    except ExternalNotebook.DoesNotExist:
        return None


def _get_external_note(guid):
    try:
        return ExternalNote.objects.get(external_id=guid)
    except ExternalNote.DoesNotExist:
        return None


def _get_external_tag(guid):
    try:
        return ExternalTag.objects.get(external_id=guid)
    except ExternalTag.DoesNotExist:
        return None


def _get_external_resource(guid):
    try:
        return ExternalEmbeddedResource.objects.get(external_id=guid)
    except ExternalEmbeddedResource.DoesNotExist:
        return None


def _create_content_file(raw_data, filename):
    with open(os.path.join(settings.MEDIA_ROOT, filename), 'w') as f:
        file_obj = File(f)
        file_obj.write(raw_data)
    return os.path.join(settings.MEDIA_ROOT, filename)


def _resource_data(data):
    return {
        'id': data.guid,
        'filename': data.attributes.fileName,
        'mime': data.mime,
        'data': {
            'body': data.data.body,
        }
    }


def _tag_data(data):
    return {
        'id': data.guid,
        'label': data.name,
    }


def _create_external_tag(datum):
    local_tag, _ = Tag.objects.get_or_create(title = datum['label'],
                                             defaults = {
                                                'slug': slugify(datum['label'])
                                             })

    external_tag = ExternalTag.objects.create(
        external_id = datum['id'],
        external_source = ExternalTag.EVERNOTE,
        local_tag = local_tag,
        label = datum['label'],
    )
    return external_tag, local_tag


def _create_image_resource(creator, data):
    mime_type = data.get('mime')
    filename = data.get('filename')
    if filename is None:
        ext = EXTENSIONS[mime_type]
        filename = str(uuid4()).replace('-', '') + ext
    file_path = _create_content_file(data['data']['body'], filename)
    img = Image.objects.create(
        name = filename,
        original_format = mime_type,
        source = 'Evernote',
        identifier = data['id'],
        creator = creator,
    )
    img.image.save(filename, File(open(file_path, 'r')))
    return img


def _create_generic_resource(creator, data):
    mime_type = data.get('mime')
    filename = data.get('filename')
    if filename is None:
        ext = EXTENSIONS[mime_type]
        filename = str(uuid4()).replace('-', '') + ext
    file_path = _create_content_file(data['data']['body'], filename)
    rsrc = GenericResource.objects.create(
        name = filename,

        original_format = mime_type,
        source = 'Evernote',
        identifier = data['id'],
        creator = creator,
    )
    rsrc.file_obj.save(filename, File(open(file_path, 'r')))
    return rsrc

def _create_external_resource(creator, data, external_note):
    if data['mime'].startswith('image'):
        resource = _create_image_resource(creator, data)
    else:
        resource = _create_generic_resource(creator, data)

    external = ExternalEmbeddedResource.objects.create(
        external_id = data['id'],
        external_source = ExternalEmbeddedResource.EVERNOTE,
        part_of = external_note,
        local_resource = resource,
    )

    return external, resource


def _create_content_relation(source, predicate_identifier, target):
    return ContentRelation.objects.create(
        source=source,
        instance_of = RDFProperty.objects.get(identifier=predicate_identifier),
        target=target,
        name='Part of note',
    )


def list_notebooks(user):
    note_store, token  = _get_note_store(user)
    notebooks = note_store.listNotebooks()
    return [{
            'name': notebook.name,
            'id': notebook.guid,
            'created': _to_datetime(notebook.serviceCreated),
            'updated': _to_datetime(notebook.serviceUpdated),
            'external_notebook': _get_external_notebook(notebook.guid),
        } for notebook in notebooks]


def list_notes(user, notebook_id=None, offset=0, max_notes = 20):
    note_store, token = _get_note_store(user)
    updated_filter = NoteFilter(order=NoteSortOrder.UPDATED,
                                notebookGuid=notebook_id)

    result_spec = NotesMetadataResultSpec(includeTitle=True,
                                          includeUpdated=True,
                                          includeAttributes=True)
    result = note_store.findNotesMetadata(token, updated_filter, offset,
                                          max_notes, result_spec)
    n = result.notes[0]
    return [{
        'title': note.title,
        'id': note.guid,
        'updated': _to_datetime(note.updated),
        'external_note': _get_external_note(note.guid),
    } for note in result.notes]


def get_tag(user, tag_id):
    note_store, token = _get_note_store(user)
    tag_data = note_store.getTag(token, tag_id)
    return _tag_data(tag_data)


def get_note(user, note_id):
    note_store, token = _get_note_store(user)
    note_data = note_store.getNote(token, note_id, True, True, True, True)

    return {
        'id': note_data.guid,
        'title': note_data.title.decode('utf-8'),
        'created': _to_datetime(note_data.created),
        'updated': _to_datetime(note_data.updated),
        'content': note_data.content.decode('utf-8'),
        'notebook_id': note_data.notebookGuid,
        'source_url': note_data.attributes.sourceURL,
        'resources': [
            _resource_data(resource) for resource in note_data.resources
        ] if note_data.resources is not None else [],
        'tags': [
            get_tag(user, tag_id) for tag_id in note_data.tagGuids
        ] if note_data.tagGuids is not None else [],
    }


def sync_note(user, note_id):
    """
    Create or update a :class:`.Note` from an Evernote note.

    Information about the remote Evernote object is stored as a linked
    :class:`.ExternalNote` instance.

    Parameters
    ----------
    user
    note_id : str
        Evernote GUID.

    Returns
    -------
    :class:`.ExternalNote`
    """
    external_note = _get_external_note(note_id)
    en_note = get_note(user, note_id)

    if en_note is None:
        raise RuntimeError('No note with id %s' % note_id)

    if external_note is None:
        external_note = ExternalNote.objects.create(
            belongs_to = user,
            external_id = note_id,
            external_source = ExternalNote.EVERNOTE,
        )

    if external_note.part_of is None:
        external_notebook, _ = ExternalNotebook.objects.get_or_create(
            external_id=en_note['notebook_id'],
            defaults={
                'external_source': ExternalNotebook.EVERNOTE,
                'belongs_to': user,
            })
        external_note.part_of = external_notebook
        external_note.save()

    created = False
    if not external_note.local_note:
        external_note.local_note = Note.objects.create(
            title = en_note['title'],
            created = en_note['created'],
            creator = user,
            content = en_note['content'],
        )
        created = True
        external_note.save()

        if en_note['source_url']:
            source_resource = ExternalResource.objects.create(
                name = en_note['title'],
                source_location = en_note['source_url'],
                identifier_type = 'url',
                creator = user,
                identifier = en_note['source_url'],
                resource_type = ExternalResource.WEBSITE,
            )
            _create_content_relation(external_note.local_note, 'P129_is_about', source_resource)

    # Update the actual content of the note. This has already been done for
    #  newly created notes.
    if not created:
        external_note.local_note.content = en_note['content']

    # Handle note resources (e.g. images, PDFs).
    for datum in en_note['resources']:
        external_resource = _get_external_resource(datum['id'])
        if external_resource is None:
            external_resource, resource = _create_external_resource(user, datum, external_note)
            _create_content_relation(resource, 'P106i_forms_part_of', external_note.local_note)

    # Import Tags from Evernote, as well.
    for tag_datum in en_note['tags']:
        external_tag = _get_external_tag(tag_datum['id'])
        if external_tag is None:
            external_tag, tag = _create_external_tag(tag_datum)
        else:
            tag = external_tag.local_tag

        if tag not in external_note.local_note.tags.all():
            external_note.local_note.tags.add(tag)

    external_note.local_note.save()
    external_note.save()    # Log update event.
    return external_note
