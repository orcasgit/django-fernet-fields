from django.db import models
from django.utils import six
from django.utils.functional import cached_property

from . import fields


class DualQuerySet(models.QuerySet):
    def update(self, **kwargs):
        for fn, encrypted_fn in six.iteritems(self._dualfields):
            if fn in kwargs:
                kwargs[encrypted_fn] = kwargs[fn]
        super(DualQuerySet, self).update(**kwargs)

    @cached_property
    def _dualfields(self):
        dualfields = getattr(self.model, '_dualfields_cache', None)
        if dualfields is None:
            dualfields = {}
            for field in self.model._meta.get_fields():
                if isinstance(field, fields.DualField):
                    encrypted_field_name = field.populate_from_field.attname
                    dualfields[field.attname] = encrypted_field_name
            self.model._dualfields_cache = dualfields
        return dualfields
