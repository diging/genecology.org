from django.db.models.signals import post_save
from django.dispatch import receiver

from concepts.models import Concept, Type
from blog.models import *

### Handle Concept and Type signals. ###

@receiver(post_save, sender=Concept)
def concept_post_save_receiver(sender, **kwargs):
    """
    When a :class:`.Concept` is saved, attempt to create a corresponding
    :class:`.Entity` instance.
    """
    instance = kwargs.get('instance', None)

    try:
        instance.entity_instance
        return
    except:
        pass

    if instance.typed:
        label_normed = instance.typed.label.lower().replace(' ', '_')
        rdf_class = RDFClass.objects.filter(identifier__icontains=label_normed).first()
        Entity(
            label=instance.label,
            concept=instance,
            instance_of=rdf_class
        ).save()
    else:
        Entity(
            label=instance.label,
            concept=instance,
            instance_of=RDFClass.objects.get(identifier='E1_CRM_Entity')
       ).save()


@receiver(post_save, sender=Type)
def type_post_save_receiver(sender, **kwargs):
    """
    When a :class:`.Type` is saved, attempt to create a corresponding
    :class:`.Entity` instance.
    """
    instance = kwargs.get('instance', None)

    try:
        instance.entity_instance
        return
    except:
        pass

    Entity(
        label=instance.label,
        concept=instance,
        instance_of=RDFClass.objects.get(identifier='E55_Type')
    ).save()
