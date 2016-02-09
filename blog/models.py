from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin, Permission
)
from django.utils.text import slugify
from markupfield.fields import MarkupField


class Post(models.Model):
    """
    A blog post.
    """

    creator = models.ForeignKey('GenecologyUser', related_name='posts')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, blank=True)
    summary = MarkupField(markup_type='markdown')
    body = MarkupField(markup_type='markdown')

    tags = models.ManyToManyField('Tag', related_name='tagged_posts')

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
        return self.tagged_posts.filter(published=True).count()


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
