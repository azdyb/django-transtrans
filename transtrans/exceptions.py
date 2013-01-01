from django.core.exceptions import ValidationError

from transtrans.helpers import get_current_language, get_default_language


class TransValidationError(ValidationError):
    def __init__(self, message, code=None, params=None, lang=None):
        if lang is None:
            lang = get_default_language()
        self.lang = lang
        super(TransValidationError, self).__init__(message, code, params)
        