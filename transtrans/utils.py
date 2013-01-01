from copy import copy

from django.db import models
from django.db.models.signals import pre_init, post_init, post_save, pre_save

from transtrans.helpers import get_current_language, get_default_language
from transtrans.fields import TranslatedField
from transtrans.slots import model_post_init, model_pre_save, model_post_save
from transtrans.methods import validate_unique, propagate_current_language
from transtrans.methods import _initialized, _new_translation, _translations_all, __repr__
from transtrans.manager import TransManager

REGISTRY = set()    # Something smarter, please...


def get_registry():
    return REGISTRY


def register(translated_model):
    registry = get_registry()
    original_model = translated_model.model
    if original_model in registry:
        return None

    registry.add(original_model)

    fields = {
        '__module__': 'transtrans.models',
        'language': models.CharField(max_length=5),
        'object': models.ForeignKey(original_model, related_name='translations'),
        '__unicode__': lambda self: self.language
    }

    unique_fields = []
    for field in translated_model.fields:
        new_field = copy(original_model._meta.get_field_by_name(field)[0])
        
        # Remove uniqueness from field and add it as unique_together within language later
        if new_field.unique:    
            unique_fields.append(new_field.name)
            new_field._unique = False
            
        original_model.add_to_class(field, TranslatedField(field))
        fields[field] = new_field
        
    model_name = 'Translated{0}'.format(original_model._meta.object_name)
    model_class = type(model_name, (models.Model, ), fields)

    # Restore unique index as unique_together within language
    for uniq_field in unique_fields:
        validation_tuple = (('language', uniq_field))
        model_class._meta.unique_together.append(validation_tuple)

    TransManager().contribute_to_class(original_model, 'objects')

    original_model.add_to_class('translated_fields', translated_model.fields)
    original_model.add_to_class('propagate_current_language', propagate_current_language)
    original_model.add_to_class('_new_translation', _new_translation)
    original_model.add_to_class('_translations_all', _translations_all)
    original_model.add_to_class('__repr__', __repr__)
    original_model.add_to_class('_initialized', _initialized)
    original_model.add_to_class('validate_unique', validate_unique) # Override validate_unique method
    
    # Magic! Don't ask...
    original_model._meta._fill_related_objects_cache()
    original_model._meta.init_name_map()

    post_init.connect(model_post_init, original_model)
    pre_save.connect(model_pre_save, original_model)
    post_save.connect(model_post_save, original_model)

    return model_class


# TODO: Really unregister -- remove all added properties
def unregister(translated_model):
    registry = get_registry()
    original_model = translated_model.model
    if original_model in registry:
        registry.remove(original_model)