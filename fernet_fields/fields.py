import base64
import hashlib

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import models
from django.utils.encoding import force_bytes, force_text
from django.utils.functional import cached_property


class EncryptedFieldMixin(models.Field):
    """A field mixin to encrypt any field type.

    @@@ TODO:
    - help with migration from non-encrypted field to encrypted field?
    - docs (no lookups)

    """
    def __init__(self, *args, **kwargs):
        key = kwargs.pop('key', None)
        keys = kwargs.pop('keys', None)
        if (key is not None) and (keys is not None):
            raise ImproperlyConfigured(
                "Cannot pass both `key` and `keys` to encrypted field.")
        if keys is None:
            if key is None:
                key = getattr(settings, 'FERNET_KEY', settings.SECRET_KEY)
            keys = [key]
        self.keys = keys
        super(EncryptedFieldMixin, self).__init__(*args, **kwargs)

    @cached_property
    def fernet_keys(self):
        return [self.convert_key(k) for k in self.keys]

    @cached_property
    def fernet(self):
        if len(self.fernet_keys) == 1:
            return Fernet(self.fernet_keys[0])
        return MultiFernet([Fernet(k) for k in self.fernet_keys])

    def convert_key(self, key):
        """Convert arbitrary string key to Fernet format."""
        if isinstance(key, bytes) and len(key) == 44 and key.endswith(b'='):
            return key
        return base64.urlsafe_b64encode(
            hashlib.sha256(force_bytes(key)).digest())

    def db_type(self, connection):
        return 'bytea'

    def get_prep_value(self, value):
        if value is not None:
            return self.fernet.encrypt(force_bytes(value))

    def get_prep_lookup(self, lookup_type, value):
        raise FieldError("Cannot perform lookups against an encrypted field.")

    def from_db_value(self, value, expression, connection, context):
        if value is not None:
            return self.to_python(
                force_text(self.fernet.decrypt(bytes(value))))

    def deconstruct(self):
        name, path, args, kwargs = super(
            EncryptedFieldMixin, self
        ).deconstruct()
        kwargs['keys'] = self.keys
        return name, path, args, kwargs


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
