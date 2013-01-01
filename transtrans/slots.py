def model_pre_init(sender, *args, **kwargs):
    pass


def model_post_init(sender, instance, **kwargs):
    instance.__initialized = True
    instance._block_translations = False


def model_pre_save(sender, instance, **kwargs):
    instance._block_translations = True


# TODO: Should be done within a transaction
def model_post_save(sender, instance, created, **kwargs):
    for trans in instance._new_translations:
        if trans.dirty:
            if created:
                trans.object = instance
            trans.save()
            trans.dirty = False
    instance._block_translations = False
    
