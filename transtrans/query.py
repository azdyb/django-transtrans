from django.db.models.query import QuerySet

from transtrans.helpers import get_current_language, get_default_language


class TranslatedQuerySet(QuerySet):
    def _filter_or_exclude(self, negate, *args, **kwargs):
        
        if get_default_language() != get_current_language():
            has_translated_fields = False   
            new_kwargs = {}
            for field in self.model.translated_fields:
                query_field = kwargs.pop(field, None)
                if query_field:
                    has_translated_fields = True
                    new_kwargs['translations__{0}'.format(field)] = query_field
            kwargs.update(new_kwargs)
            
            # Only add language, if translated fields are queried 
            if has_translated_fields and 'translations__language' not in kwargs.keys():
                kwargs['translations__language'] = get_current_language()
        
        return super(TranslatedQuerySet, self)._filter_or_exclude(negate, *args, **kwargs)