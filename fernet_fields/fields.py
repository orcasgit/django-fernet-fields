from cryptography.fernet import Fernet
from django.core.exceptions import FieldError
from django.db import models
from django.utils.encoding import force_bytes, force_text
from django.utils.functional import cached_property


class EncryptedFieldMixin(models.Field):
    """A field mixin to encrypt any field type.

    @@@ TODO:
    - prevent lookups
    - handle migration when secret changes?
    - help with migration from non-encrypted field to encrypted field?
    - default secret key to a setting
    - docs (no lookups)

    """
    def __init__(self, *args, **kwargs):
        self.key = kwargs.pop('key')
        super(EncryptedFieldMixin, self).__init__(*args, **kwargs)

    @cached_property
    def fernet(self):
        return Fernet(self.key)

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
        kwargs['key'] = self.key
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
