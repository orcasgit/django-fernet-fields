from hashlib import sha256

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import models
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
        if kwargs.get('primary_key'):
            raise ImproperlyConfigured(
                "EncryptedFieldMixin does not support primary_key=True."
            )
        if kwargs.get('unique'):
            raise ImproperlyConfigured(
                "EncryptedFieldMixin does not support unique=True."
            )
        if kwargs.get('db_index'):
            raise ImproperlyConfigured(
                "EncryptedFieldMixin does not support db_index=True."
            )
        super(EncryptedFieldMixin, self).__init__(*args, **kwargs)

    @cached_property
    def keys(self):
        keys = getattr(settings, 'FERNET_KEYS', None)
        if keys is None:
            keys = [settings.SECRET_KEY]
        return keys

    @cached_property
    def fernet_keys(self):
        if getattr(settings, 'FERNET_USE_HKDF', True):
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

    def get_db_prep_save(self, value, connection):
        value = super(
            EncryptedFieldMixin, self
        ).get_db_prep_save(value, connection)
        if value is not None:
            retval = self.fernet.encrypt(force_bytes(value))
            return connection.Database.Binary(retval)

    def get_prep_lookup(self, lookup_type, value):
        raise FieldError(
            "Encrypted field '%s' does not support lookups." % self.name
        )

    def from_db_value(self, value, expression, connection, context):
        if value is not None:
            value = bytes(value)
            return self.to_python(force_text(self.fernet.decrypt(value)))


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


class HashField(models.Field):
    def __init__(self, populate_from, *args, **kwargs):
        self.populate_from = populate_from
        super(HashField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        # PostgreSQL and SQLite both support the BYTEA type.
        return 'bytea'

    def get_internal_type(self):
        """Prevent Django attempting type conversions on hashed data."""
        return None

    def get_db_prep_value(self, value, connection, *a, **kw):
        value = super(
            HashField, self
        ).get_db_prep_value(value, connection, *a, **kw)
        if value is not None:
            retval = sha256(force_bytes(value)).digest()
            return connection.Database.Binary(retval)

    @cached_property
    def populate_from_field(self):
        return self.model._meta.get_field(self.populate_from)

    def pre_save(self, instance, add):
        return self.populate_from_field.value_from_object(instance)

    def get_prep_lookup(self, lookup_type, value):
        if lookup_type not in {'exact', 'in', 'isnull'}:
            raise FieldError(
                "HashField '%s' supports only exact, in, and isnull lookups."
                % self.name
            )
        return super(HashField, self).get_prep_lookup(lookup_type, value)
