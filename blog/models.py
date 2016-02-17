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


class ContentRelation(models.Model):
    name = models.CharField(max_length=1000)
    description = MarkupField(markup_type='markdown', blank=True)

    source_content_type = models.ForeignKey(ContentType, related_name='as_source')
    source_instance_id = models.IntegerField(default=0)
    source = GenericForeignKey('source_content_type', 'source_instance_id')

    target_content_type = models.ForeignKey(ContentType, related_name='as_target')
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


class Note(Content):
    """
    """

    content = MarkupField(markup_type='markdown')


class ConceptProfile(Content):
    concept = models.ForeignKey(Concept, related_name='profile')

    description = MarkupField(markup_type='markdown')


class Resource(Content):
    source = models.CharField(max_length=1000)
    identifier = models.CharField(max_length=1000)
    identifier_type = models.CharField(max_length=1000)
    description = MarkupField(markup_type='markdown')

    class Meta:
        abstract = True


class Image(Resource):
    image = models.FileField(upload_to='images/')
    original_format = models.CharField(max_length=255)


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
