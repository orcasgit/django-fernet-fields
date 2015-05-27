from django.db import models
from django.utils import six
from django.utils.functional import cached_property

from . import fields


__all__ = [
    'DualQuerySet',
    'DualManager',
]


class DualQuerySet(models.QuerySet):
    def update(self, **kwargs):
        # Ensure that an update to a DualField updates its associated
        # EncryptedField, too.
        for fn, encrypted_fn in six.iteritems(self._dualfields):
            if fn in kwargs:
                kwargs[encrypted_fn] = kwargs[fn]
        super(DualQuerySet, self).update(**kwargs)

    @cached_property
    def _dualfields(self):
        """Return a mapping of dualfield-name -> encryptedfield-name."""
        dualfields = getattr(self.model, '_dualfields_cache', None)
        if dualfields is None:
            dualfields = {}
            for field in self.model._meta.get_fields():
                if isinstance(field, fields.DualField):
                    dualfields[field.attname] = field.encrypted_field.attname
            self.model._dualfields_cache = dualfields
        return dualfields


DualManager = models.Manager.from_queryset(DualQuerySet)
