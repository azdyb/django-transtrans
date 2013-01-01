from django.utils import translation
from django.conf import settings


class TranslationErrorKey(str):
    pass

class TranslationErrorValue(unicode):
    pass


def get_current_language():
    current_language = translation.get_language()
    #TODO: Do magic
    return current_language


def get_default_language():
    #TODO: Implement
    return 'en'


def get_active_languages():
    lang_codes = [l[0] for l in settings.LANGUAGES]
    return sorted(lang_codes, reverse=True)


# TODO: Left only as a reminder to implement it properly
# Not used for now
def __gettranslatedattr__(self, name):
    tokens = name.split('__')
    if len(tokens) == 2:
        if tokens[0] in self.translated_fields:
            for trans in self.translations.all():
                if trans.language == tokens[1]:
                    return getattr(trans, tokens[0])
            return getattr(self, tokens[0])
    raise AttributeError


def langcode_normalize(lang):
    return lang.replace("-", "_")


def langcode_denormalize(lang):
    return lang.replace("_", "-")
