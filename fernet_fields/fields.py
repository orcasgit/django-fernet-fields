from hashlib import sha256

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import models
from django.db.models import lookups
from django.utils.encoding import force_bytes, force_text
from django.utils.functional import cached_property

from . import hkdf


__all__ = [
    'EncryptedFieldMixin',
    'EncryptedTextField',
    'EncryptedCharField',
    'EncryptedEmailField',
    'EncryptedIntegerField',
    'EncryptedDateField',
    'EncryptedDateTimeField',
]


class EncryptedFieldMixin(models.Field):
    """A field mixin to encrypt values using Fernet symmetric encryption."""
    def __init__(self, *args, **kwargs):
        unique = kwargs.pop('unique', False)
        db_index = kwargs.pop('db_index', False)
        if kwargs.get('primary_key'):
            raise ImproperlyConfigured(
                "EncryptedFieldMixin does not support primary_key=True."
            )
        key = kwargs.pop('key', None)
        keys = kwargs.pop('keys', None)
        self.use_hkdf = kwargs.pop(
            'use_hkdf', getattr(settings, 'FERNET_USE_HKDF', True))
        if (key is not None) and (keys is not None):
            raise ImproperlyConfigured(
                "Cannot pass both `key` and `keys` to encrypted field.")
        if keys is None:
            if key is not None:
                keys = [key]
            else:
                keys = getattr(settings, 'FERNET_KEYS', None)
                if keys is None:
                    keys = [settings.SECRET_KEY]
        self.keys = keys
        super(EncryptedFieldMixin, self).__init__(*args, **kwargs)
        self.prepend_hash = None
        if unique:
            self.prepend_hash = 'unique'
        elif db_index:
            self.prepend_hash = 'index'

    @cached_property
    def fernet_keys(self):
        if self.use_hkdf:
            return [hkdf.derive_fernet_key(k) for k in self.keys]
        return self.keys

    @cached_property
    def fernet(self):
        if len(self.fernet_keys) == 1:
            return Fernet(self.fernet_keys[0])
        return MultiFernet([Fernet(k) for k in self.fernet_keys])

    def db_type(self, connection):
        # PostgreSQL and SQLite both support the BYTEA type.
        return 'bytea'

    def get_internal_type(self):
        """Prevent Django attempting type conversions on encrypted data."""
        return None

    def get_db_prep_save(self, *args, **kwargs):
        value = super(
            EncryptedFieldMixin, self
        ).get_db_prep_value(*args, **kwargs)
        if value is not None:
            value = force_bytes(value)
            retval = self.fernet.encrypt(value)
            if self.prepend_hash:
                retval = sha256(value).digest() + retval
            return retval

    def get_prep_lookup(self, lookup_type, value):
        if self.prepend_hash and lookup_type in {'exact', 'in'}:
            if lookup_type == 'in':
                return [self.get_prep_lookup('exact', v) for v in value]
            return sha256(force_bytes(value)).digest()
        raise FieldError(
            "Encrypted field only supports exact and __in lookups, "
            "and only if field is indexed."
        )

    def from_db_value(self, value, expression, connection, context):
        if value is not None:
            value = bytes(value)
            if self.prepend_hash:
                value = value[32:]
            return self.to_python(force_text(self.fernet.decrypt(value)))

    def deconstruct(self):
        name, path, args, kwargs = super(
            EncryptedFieldMixin, self
        ).deconstruct()
        kwargs['keys'] = self.keys
        return name, path, args, kwargs


class HashPrefixLookupMixin(object):
    def process_lhs(self, compiler, connection):
        lhs, params = super(
            HashPrefixLookupMixin, self
        ).process_lhs(compiler, connection)
        return 'SUBSTRING(%s for 32)' % lhs, params


class HashPrefixExact(HashPrefixLookupMixin, lookups.Exact):
    pass


EncryptedFieldMixin.register_lookup(HashPrefixExact)


class HashPrefixIn(HashPrefixLookupMixin, lookups.In):
    pass


EncryptedFieldMixin.register_lookup(HashPrefixIn)


class EncryptedTextField(EncryptedFieldMixin, models.TextField):
    pass


class EncryptedCharField(EncryptedFieldMixin, models.CharField):
    pass


class EncryptedEmailField(EncryptedFieldMixin, models.EmailField):
    pass


class EncryptedIntegerField(EncryptedFieldMixin, models.IntegerField):
    pass


class EncryptedDateField(EncryptedFieldMixin, models.DateField):
    pass


class EncryptedDateTimeField(EncryptedFieldMixin, models.DateTimeField):
    pass
