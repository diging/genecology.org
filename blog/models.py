from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin, Permission
)
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from markupfield.fields import MarkupField

from concepts.models import Concept, Type

from reversion import revisions as reversion

import re
import bleach


def help_text(s):
    """
    Cleans up help strings so that we can write them in ways that are
    human-readable without screwing up formatting in the admin interface.
    """
    return re.sub('\s+', ' ', s).strip()


class ContentRelation(models.Model):
    instance_of = models.ForeignKey('RDFProperty',
                                    related_name='content_relations',
                                    blank=True, null=True,
                                    help_text=help_text("""
    Each relation should have a formal type or property from a controlled
    vocabulary. If you don't see an appropriate option here, we chould consider
    loading additional vocabularies or, if absolutely necessary, creating our
    own."""))

    name = models.CharField(max_length=1000, blank=True, null=True,
                            help_text=help_text("""
    Descriptive name for the relation. E.g. "elaborates on", "provides context
    for", "is related to"."""))

    description = MarkupField(markup_type='markdown', blank=True,
                              help_text=help_text("""
    If appropriate, provide further elaboration on the nature of the relation.
    """))

    source_content_type = models.ForeignKey(ContentType,
                                            related_name='as_source')
    source_instance_id = models.IntegerField(default=0)
    source = GenericForeignKey('source_content_type', 'source_instance_id')

    target_content_type = models.ForeignKey(ContentType,
                                            related_name='as_target')
    target_instance_id = models.IntegerField(default=0)
    target = GenericForeignKey('target_content_type', 'target_instance_id')


class Content(models.Model):
    class Meta:
        abstract = True

    creator = models.ForeignKey('GenecologyUser')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    about = models.ManyToManyField(Concept, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)

    slug = models.SlugField(max_length=100, blank=True)

    relations_from = GenericRelation('ContentRelation',
                                     related_query_name='source_content',
                                     content_type_field='source_content_type',
                                     object_id_field="source_instance_id")

    relations_to = GenericRelation('ContentRelation',
                                    related_query_name='target_content',
                                    content_type_field='target_content_type',
                                    object_id_field="target_instance_id")

    instance_of = models.ForeignKey('RDFClass',
                                    blank=True, null=True)


class Note(Content):
    """
    """
    title = models.CharField(max_length=255)
    content = MarkupField(markup_type='markdown')

    @property
    def summary(self):
        content = self._content_rendered[:200] + u'...'
        return bleach.clean(content, tags=[], strip=True).replace('\n', ' ')

    @property
    def content_clean(self):
        return bleach.clean(self.content, tags=[], strip=True)


class ConceptProfile(Content):
    concept = models.OneToOneField(Concept, related_name='profile')
    summary = MarkupField(markup_type='markdown')
    description = MarkupField(markup_type='markdown')

    @property
    def description_clean(self):
        return bleach.clean(self.description, tags=[], strip=True)


class Resource(Content):
    name = models.CharField(max_length=255, help_text=help_text("""
    If available, use the original title of the resource. Otherwise, create a
    concise but descriptive title (e.g. "James Gregor obituary").
    """))

    source = models.CharField(max_length=1000, help_text=help_text("""
    Name of the source (e.g. name of a newspaper, website).
    """))

    source_location = models.URLField(max_length=500, blank=True, null=True,
                                      help_text=help_text("""
    For online resources, this should be the location of the resource. For
    archives, this should be a link to the finding aid, if available.
    """))

    identifier = models.CharField(max_length=1000, help_text=help_text("""
    The unique identifier used to refer to the original resource. For archives,
    this could be a collection/bundle/item identifier. For web resources, this
    coud be the URL (i.e. same as source location).
    """))

    IDENTIFIER_TYPE_CHOICES = (
        ('url', 'URL'),
        ('uri', 'URI'),
        ('archive', 'Archival identifier'),
        ('catalog', 'Library catalog identifier'),
        ('doi', 'DOI'),
        ('handle', 'Handle'),
        ('isbn', 'ISBN'),
        ('issn', 'ISSN'),
        ('other', 'Other')
    )
    identifier_type = models.CharField(choices=IDENTIFIER_TYPE_CHOICES,
                                       max_length=1000)
    description = MarkupField(markup_type='markdown', help_text=help_text("""
    Depends on the resource type. To quote the original resource, use the
    markdown blockquote, e.g. "&gt; Here is some quoted text".
    """))

    class Meta:
        abstract = True


class ExternalResource(Resource):
    RESOURCE_TYPES = (
        ('WB', 'Website'),
        ('JO', 'Journal article'),
        ('BK', 'Book'),
        ('PE', 'Periodical article'),
        ('DT', 'Dataset'),
        ('AR', 'Archive'),
        ('OT', 'Other'),
    )
    resource_type = models.CharField(max_length=2, choices=RESOURCE_TYPES)
    created_original =  models.DateField(verbose_name='original creation date',
                                         help_text=help_text("""
    Date on which the original resource was created. For example, the
    publication date of an article.
    """))


class Image(Resource):
    image = models.FileField(upload_to='images/', null=True, blank=True,
                             help_text=help_text("""
    If appropriate, upload a digital copy of the image here."""))

    remote = models.URLField(max_length=500, null=True, blank=True,
                             help_text=help_text("""
    If it is not possible to upload a copy of the image, enter the remote
    location of the image here."""))

    original_format = models.CharField(max_length=255, help_text=help_text("""
    If possible, this should be a MIME-type (e.g. image/jpeg)."""))

    @property
    def location(self):
        """

        """
        if self.image:
            return self.image
        return self.remote


class Data(Resource):
    FORMAT_CHOICES = (
        ('csv', 'Comma-separated'),
    )
    data_format = models.CharField(max_length=3, choices=FORMAT_CHOICES)
    location = models.CharField(max_length=500)

    class Meta:
        verbose_name = 'datum'
        verbose_name_plural = 'data'


class Post(Content):
    """
    A blog post.
    """

    title = models.CharField(max_length=255)

    summary = MarkupField(markup_type='markdown')
    body = MarkupField(markup_type='markdown')

    published = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)[:100]
        super(Post, self).save(*args, **kwargs)

    @property
    def title_condensed(self):
        return self.title[:50] + u'...'

    @property
    def body_clean(self):
        return bleach.clean(self.body, tags=[], strip=True)

    def __unicode__(self):
        return self.title


class Tag(models.Model):
    slug = models.SlugField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField()

    def __unicode__(self):
        return self.slug

    def num_posts(self):
        return self.post_set.filter(published=True).count()


class GenecologyUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(
            username,
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class GenecologyUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
    )

    affiliation = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    link = models.URLField(max_length=500, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    bio = MarkupField(markup_type='markdown')

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = GenecologyUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.username

    def __unicode__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class RDFSchema(models.Model):
    name = models.CharField(max_length=255)

    namespace = models.CharField(max_length=255, blank=True, null=True)
    uri = models.CharField(max_length=255, blank=True, null=True,
                           verbose_name='URI')

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        verbose_name = 'RDF schema'
        verbose_name_plural = 'RDF schemas'

class RDFClass(models.Model):
    """
    """
    label = models.CharField(max_length=255, blank=True, null=True)
    identifier = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)

    subClassOf = models.ForeignKey('RDFClass', related_name='superClassOf', blank=True, null=True)

    partOf = models.ForeignKey('RDFSchema', related_name='classes')

    class Meta:
        verbose_name = 'RDF class'
        verbose_name_plural = 'RDF classes'

    def __unicode__(self):
        if self.label:
            return self.label
        return self.identifier


class RDFProperty(models.Model):
    """
    """
    label = models.CharField(max_length=255, blank=True, null=True)
    identifier = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)

    subPropertyOf = models.ForeignKey('RDFProperty', related_name='superPropertyOf', blank=True, null=True)

    domain = models.ForeignKey('RDFClass', related_name='in_domain_of', null=True, blank=True, verbose_name='domain')
    range = models.ForeignKey('RDFClass', related_name='in_range_of', null=True, blank=True, verbose_name='range')

    partOf = models.ForeignKey('RDFSchema', related_name='properties',
                               verbose_name='part of')

    class Meta:
        verbose_name = 'RDF property'
        verbose_name_plural = 'RDF properties'

    def __unicode__(self):
        if self.label:
            return self.label
        return self.identifier


class Entity(models.Model):
    """
    """
    creator = models.ForeignKey('GenecologyUser', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


    label = models.CharField(max_length=255)
    concept = models.OneToOneField(Concept, null=True, blank=True, related_name='entity_instance')
    instance_of = models.ForeignKey('RDFClass', related_name='instances')

    class Meta:
        verbose_name_plural = 'entities'

    def __unicode__(self):
        return self.label

    def is_a(self, target_class):
        """
        Evaluates whether this :class:`.Entity` is an instance of
        the :class:`.RDFClass` instance ``target_class`` (including its
        descendants).
        """

        def traverse_up(rdf_class):     # Collects all ancestor RDFClasses.
            if rdf_class.subClassOf:
                return [rdf_class] + traverse_up(rdf_class.subClassOf)
            return [rdf_class]    # Reached the highest level of the lineage.

        return target_class in traverse_up(self.instance_of)


class Property(models.Model):
    creator = models.ForeignKey('GenecologyUser', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    concept = models.OneToOneField(Concept, related_name='property_instance',
                                   blank=True, null=True)
    instance_of = models.ForeignKey('RDFProperty', related_name='instances',
                                    verbose_name='property type',
                                    help_text=help_text("""
    Each relation should have a formal type or property from a controlled
    vocabulary. If you don't see an appropriate option here, we chould consider
    loading additional vocabularies or, if absolutely necessary, creating our
    own. **Important** be sure to select a relationship with the appropriate
    domain and range! The domain should match the type of the "source" entity
    (e.g. Person) and the range should match the type of the "target" entity.
    """))
    source = models.ForeignKey('Entity', related_name='properties_from')
    target = models.ForeignKey('Entity', related_name='properties_onto')

    class Meta:
        verbose_name_plural = 'properties'

    def __unicode__(self):
        return self.instance_of.__unicode__()

    def is_a(self, rdfproperty):
        """
        Evaluates whether this :class:`.Property` is an instance of
        the :class:`.RDFPropery` instance ``rdfproperty`` (including its
        descendants).

        TODO: implement this.
        """
        return


reversion.register(ContentRelation)
reversion.register(Note)
reversion.register(Tag)
reversion.register(ConceptProfile)
reversion.register(Image)
reversion.register(Post)
reversion.register(Data)
