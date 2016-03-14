from django.core.urlresolvers import reverse

from rest_framework import serializers

from blog.models import *
from concepts.models import *

import bleach


class ConceptProfileURLField(serializers.Field):
    def to_representation(self, obj):
        return reverse('person', args=(obj,))


class BleachyCleanField(serializers.Field):
    """
    Strips HTML tags.
    """
    def to_representation(self, obj):
        return bleach.clean(obj, tags=[], strip=True).replace('\n', ' ')


class TypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        exclude = ('description', 'resolved', 'real_type', 'concept_state')


class TypeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        exclude = ('resolved', 'real_type', 'concept_state')


class ConceptListSerializer(serializers.ModelSerializer):
    typed = TypeListSerializer()

    class Meta:
        model = Concept
        exclude = ('resolved', 'real_type', 'concept_state')


class ConceptDetailSerializer(serializers.ModelSerializer):
    typed = TypeDetailSerializer()

    class Meta:
        model = Concept
        exclude = ('resolved', 'real_type', 'concept_state')


class GenecologyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenecologyUser
        fields = ('id', 'username', 'full_name')


class PostSerializer(serializers.ModelSerializer):
    creator = GenecologyUserSerializer()
    summary = BleachyCleanField()
    about = ConceptListSerializer(many=True)

    class Meta:
        model = Post
        exclude = ('_summary_rendered', '_body_rendered', 'body_markup_type', 'summary_markup_type')


class PostListSerializer(PostSerializer):
    class Meta:
        model = Post
        exclude = ('body', '_summary_rendered', '_body_rendered', 'tags', 'published', 'body_markup_type', 'summary_markup_type')


class TagSerializer(serializers.ModelSerializer):
    tagged_posts = PostListSerializer(many=True, source='post_set')

    class Meta:
        model = Tag
        fields = ('id', 'slug', 'title', 'description', 'tagged_posts')


class TagListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'slug', 'title',)


class PostDetailSerializer(PostSerializer):
    body = BleachyCleanField()
    tags = TagListSerializer(many=True)


class ConceptProfileListSerializer(serializers.ModelSerializer):
    summary = BleachyCleanField()
    creator = GenecologyUserSerializer()
    tags = TagListSerializer(many=True)
    concept = ConceptListSerializer()
    url = ConceptProfileURLField(source='id')

    class Meta:
        model = ConceptProfile
        exclude = (
            'description_markup_type',
            '_description_rendered',
            'about',
            'description',
            'summary_markup_type',
            '_summary_rendered',
        )
