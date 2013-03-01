from collections import namedtuple

from django.core.exceptions import ValidationError
from django.utils.text import get_text_list, capfirst
from django.utils.translation import ugettext_lazy as _

from transtrans.exceptions import TransValidationError
from transtrans.helpers import get_default_language, TranslationErrorKey, TranslationErrorValue


def _initialized(self):
    if not hasattr(self, '__initialized'):
        setattr(self, '__initialized', False)
    return self.__initialized


def _new_translation(self):
    model = self.__class__
    translation_model = model.translations.related.model
    translation = translation_model(object=self)
    translation.dirty = True
    return translation


# Primitive cache for translations
def _translations_all(self):
    try:
        return self.__translations_all
    except AttributeError:
        self.__translations_all = self.translations.all()
        return self.__translations_all


# TODO: Add possibility for not committing (save) 
def propagate_current_language(self):
    kwargs = {}
    for field_name in self.translated_fields:
        kwargs[field_name] = getattr(self, field_name)
        
    for trans in self._new_translations:
        trans.dirty = False
    
    for attr, val in kwargs.items():
        self.__dict__[attr] = val
    self.save()
    self.translations.update(**kwargs)

        
# Needed for tools like debug_toolbar and debuggers not break caching
def __repr__(self):
    blocked = self._block_translations
    self._block_translations = True
    repr = super(self.__class__, self).__repr__()
    self._block_translations = blocked
    return repr


def validate_unique(self, exclude=None):
    if exclude is None:
        exclude = []
        
    # First, check all non-translated fields
    # Note, it will stop processing other validations if it throws ValidationError
    super(self.__class__, self).validate_unique(list(self.translated_fields) + exclude)
    
    # No validation errors so far, let's check multilanguage fields
    # Check fields for default language (stored in original table)
    errors = {}
    unique_checks = []
    self._block_translations = True
    for field_name in self.translated_fields:
        field = self._meta.get_field(field_name)
        if field.unique:    # FIXME: This will break any other validations
            new_errors = is_trans_uniq(self, (field_name, ))
            for key, val in new_errors.items():
                errors.setdefault(key, [])
                errors[key] += val
    self._block_translations = False
    
    # Now take care of translated fields
    # Do it naive way
    for trans in self._new_translations:
        if trans.dirty:
            for uniq in trans._meta.unique_together:
                new_errors = is_trans_uniq(trans, uniq)
                for key, val in new_errors.items():
                    errors.setdefault(key, [])
                    errors[key] += val

    if errors:
        raise TransValidationError(errors)

        
def is_trans_uniq(trans, uniq):
    errors = {}
    lookup_kwargs = {}
    for field_name in uniq:
        field_value = getattr(trans, field_name)
        if field_value is not None:
            lookup_kwargs[field_name] = field_value 
    qs = trans.__class__._default_manager.filter(**lookup_kwargs)
    if not trans._state.adding and trans.pk is not None:
        qs = qs.exclude(pk=trans.pk)
    
    if qs.exists():
        if len(uniq) == 1:
            key = TranslationErrorKey(uniq[0])
            key.lang = get_default_language()
        else:
            key = TranslationErrorKey(uniq[1])
            key.lang = trans.language
        err = _(u"%(field_name)s is not unique within this translation (%(lang)s)") \
            % {'field_name': capfirst(unicode(field_name)), 'lang': key.lang}
        err = TranslationErrorValue(err)
        err.lang = key.lang
        errors.setdefault(key, []).append(err)
    return errors

