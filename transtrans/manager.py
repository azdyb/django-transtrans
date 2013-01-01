from django.db import models
from transtrans.query import TranslatedQuerySet

class TransManager(models.Manager):

    def get_query_set(self):
        return TranslatedQuerySet(self.model, using=self._db).prefetch_related('translations')
