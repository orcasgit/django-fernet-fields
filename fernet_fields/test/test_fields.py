from cryptography.fernet import Fernet
from datetime import date, datetime

from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import connection
from django.utils.encoding import force_bytes, force_text
import pytest

import fernet_fields as fields
from . import models


class TestEncryptedField(object):
    def test_deconstruct(self):
        f = fields.EncryptedTextField(key='secret')

        assert f.deconstruct()[3]['keys'] == ['secret']

    def test_key_from_settings(self, settings):
        """If no key is provided for a field, use settings.FERNET_KEY."""
        settings.FERNET_KEY = 'fernet'
        f = fields.EncryptedTextField()

        assert f.keys == [settings.FERNET_KEY]

    def test_fallback_to_secret_key(self, settings):
        """If no key given and no FERNET_KEY setting, use SECRET_KEY."""
        f = fields.EncryptedTextField()

        assert f.keys == [settings.SECRET_KEY]

    def test_key_rotation(self):
        """Can supply multiple `keys` for key rotation."""
        f = fields.EncryptedTextField(keys=['key1', 'key2'])

        enc1 = Fernet(f.fernet_keys[0]).encrypt(b'enc1')
        enc2 = Fernet(f.fernet_keys[1]).encrypt(b'enc2')

        assert f.fernet.decrypt(enc1) == b'enc1'
        assert f.fernet.decrypt(enc2) == b'enc2'

    def test_cannot_supply_both_key_and_keys(self):
        with pytest.raises(ImproperlyConfigured):
            fields.EncryptedTextField(key='foo', keys=['a', 'b'])

    def test_raw_key(self):
        """Can supply raw_key=True to avoid HKDF."""
        k1 = Fernet.generate_key()
        f = fields.EncryptedTextField(key=k1, raw_keys=True)
        fernet = Fernet(k1)

        assert fernet.decrypt(f.fernet.encrypt(b'foo')) == b'foo'

    def test_primary_key_not_allowed(self):
        with pytest.raises(ImproperlyConfigured):
            fields.EncryptedIntegerField(primary_key=True, key='secret')

    def test_unique_not_allowed(self):
        with pytest.raises(ImproperlyConfigured):
            fields.EncryptedIntegerField(unique=True, key='secret')

    def test_db_index_not_allowed(self):
        with pytest.raises(ImproperlyConfigured):
            fields.EncryptedIntegerField(db_index=True, key='secret')


@pytest.mark.parametrize(
    'model,vals',
    [
        (models.EncryptedText, ['foo', 'bar']),
        (models.EncryptedChar, ['one', 'two']),
        (models.EncryptedEmail, ['a@example.com', 'b@example.com']),
        (models.EncryptedInt, [1, 2]),
        (models.EncryptedDate, [date(2015, 2, 5), date(2015, 2, 8)]),
        (
            models.EncryptedDateTime,
            [datetime(2015, 2, 5, 15), datetime(2015, 2, 8, 16)],
        ),
    ],
)
class TestEncryptedFieldQueries(object):
    def test_insert(self, db, model, vals):
        """Data stored in DB is actually encrypted."""
        field = model._meta.get_field('value')
        model.objects.create(value=vals[0])
        with connection.cursor() as cur:
            cur.execute('SELECT value FROM %s' % model._meta.db_table)
            data = [
                force_text(field.fernet.decrypt(force_bytes(r[0])))
                for r in cur.fetchall()
            ]

        assert list(map(field.to_python, data)) == [vals[0]]

    def test_insert_and_select(self, db, model, vals):
        """Data round-trips through insert and select."""
        model.objects.create(value=vals[0])
        found = model.objects.get()

        assert found.value == vals[0]

    def test_update_and_select(self, db, model, vals):
        """Data round-trips through update and select."""
        model.objects.create(value=vals[0])
        model.objects.update(value=vals[1])
        found = model.objects.get()

        assert found.value == vals[1]

    def test_lookups_raise_field_error(self, db, model, vals):
        """Lookups are not allowed (they cannot succeed)."""
        model.objects.create(value=vals[0])

        with pytest.raises(FieldError):
            model.objects.get(value=vals[0])


def test_nullable(db):
    """Encrypted field can be nullable."""
    models.EncryptedInt.objects.create(value=None)
    found = models.EncryptedInt.objects.get()

    assert found.value is None
