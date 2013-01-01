from transtrans.helpers import get_current_language, get_default_language


class TranslatedField(object):
    def __init__(self, field_name):
        self.field_name = field_name

    def __get__(self, instance, owner):
        if instance._block_translations:
            return self.default_value(instance)

        curr_lang = get_current_language()
        if curr_lang == instance._initial_language:
            return self.default_value(instance)

        for trans in instance._new_translations:
            if trans.language == curr_lang:
                return getattr(trans, self.field_name)

        # FIME: Probably should use instance._state.adding instead of testing pk == None
        if instance.pk is not None:
            for trans in instance._translations_all():
                if trans.language == curr_lang:
                    return getattr(trans, self.field_name)

        return self.default_value(instance)

    def __set__(self, instance, value):        
        curr_lang = get_current_language()
        default_lang = get_default_language()

        if not hasattr(instance, '_new_translations'):
            instance._new_translations = []

        if not instance._initialized() and instance.pk is not None:
            instance._initial_language = default_lang
            instance.__dict__[self.field_name] = value
            return

        if not hasattr(instance, '_initial_language'):
            if instance.pk is None:
                instance._initial_language = get_current_language()
            else:
                instance._initial_language = get_default_language()
                instance.__dict__[self.field_name] = value

        if curr_lang == default_lang:
            instance._initial_language = curr_lang

        if curr_lang == instance._initial_language:
            instance.__dict__[self.field_name] = value

        for trans in instance._new_translations:
            if trans.language == curr_lang:
                setattr(trans, self.field_name, value)
                trans.dirty = True
                return

        # FIME: Probably should use instance._state.adding instead of testing pk == None
        if instance.pk is not None and instance._initialized():
            for trans in instance._translations_all():
                if trans.language == curr_lang:
                    setattr(trans, self.field_name, value)
                    trans.dirty = True
                    instance._new_translations.append(trans)
                    return

        # Create translation if not found
        new_translation = instance._new_translation()
        setattr(new_translation, self.field_name, value)
        new_translation.language = curr_lang
        instance._new_translations.append(new_translation)


    def default_value(self, instance):
        return instance.__dict__[self.field_name]