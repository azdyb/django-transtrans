from copy import copy

from django import forms
from django.forms.models import ModelFormMetaclass
from django.utils import translation
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS

from transtrans.helpers import get_active_languages, get_current_language, TranslationErrorKey, TranslationErrorValue
from transtrans.exceptions import TransValidationError


class MultilanguageModelFormMetaclass(ModelFormMetaclass):

    def __new__(cls, name, bases, attrs):
        new_class = ModelFormMetaclass.__new__(cls, name, bases, attrs)
        new_class.multi_language_fields = getattr(attrs.get('Meta', None), 'multi_language_fields', None)
        return new_class


class MultilanguageModelForm(forms.ModelForm):
    __metaclass__ = MultilanguageModelFormMetaclass

    def __init__(self, *args, **kwargs):
        """
        Probably should be moved to Metaclass
        """

        self.languages = kwargs.pop('languages', get_active_languages())
        multi_language_fields = self.multi_language_fields or []
        
        # Walk through all fields and split multilanguage ones
        field_index = 0
        for field_name, field in self.base_fields.items():
            if field_name in multi_language_fields:
                # Create a field copy for each language
                for lang in self.languages:
                    key = '{field_name}_{lang}'.format(field_name=field_name, lang=lang)
                    new_field = copy(field)
                    new_field.label = self.label_for_field(new_field, lang)
                    self.base_fields.insert(field_index, key, new_field)
                    field_index += 1
                del self.base_fields[field_name]
            else:
                # For non-multilanguage fields just move them to proper position
                field = self.base_fields.pop(field_name)    # FIXME: Ugly but works for now
                self.base_fields.insert(field_index, field_name, field)
            field_index += 1
            
        # Now take care of initial data
        initial = {}
        orig_lang = get_current_language()
        
        if 'instance' in kwargs:
            for lang in self.languages:
                translation.activate(lang)
                for field_name in multi_language_fields:
                    name =  '{name}_{lang}'.format(name=field_name, lang=lang)
                    initial[name] = getattr(kwargs['instance'], field_name)

        initial.update(kwargs.get('initial', {}))
        kwargs['initial'] = initial
        translation.activate(orig_lang) # Restore saved language
        super(MultilanguageModelForm, self).__init__(*args, **kwargs)


    def label_for_field(self, field, lang):
        return u'{label} ({lang})'.format(label=field.label, lang=lang)

    
    def _post_clean(self):
        # Default implementation is empty, but for the record...
        super(MultilanguageModelForm, self)._post_clean()

        if not self.is_valid():
            return

        orig_lang = get_current_language()  # Save language
        
        # For all configured languages
        for lang in self.languages:
            translation.activate(lang)
            suffix = "_{0}".format(lang)
            for lang_field_name in self.changed_data:    # FIXME: Walk only through configured fields
                if lang_field_name.endswith(suffix):
                    field_name = lang_field_name[:-len(suffix)]
                    setattr(self.instance, field_name, self.cleaned_data[lang_field_name])
        
        translation.activate(orig_lang)     # Restore saved language
        
        # FIXME: Find more efficient way
        if self._validate_unique:
            self.validate_unique()
            

    def validate_unique(self):
        """
        Checks if error concerns a translation and if so,
        adds suffix for language
        """
        exclude = self._get_validation_exclusions()
        try:
            # Repeat instance validation
            # This is highly inefficient
            # TODO: Need to find a way to avoid this 
            self.instance.validate_unique(exclude=exclude)
        except TransValidationError as e:
            error_messages = {}
            # Walk through all errors found by validate_unique
            for field_name, error_values in e.message_dict.items():
                if field_name == NON_FIELD_ERRORS:  # skip form errors
                    continue
                
                for err in error_values:
                    # Add suffix for language
                    if isinstance(err, TranslationErrorValue):
                        key = "{0}_{1}".format(field_name, err.lang)
                        error_messages.setdefault(key, []).append(err)
                    else:
                        key = "{0}_{1}".format(field_name, e.lang)
                        error_messages.setdefault(key, []).append(err)

            self._update_errors(error_messages)
        except ValidationError, e:
            self._update_errors(e.message_dict)
