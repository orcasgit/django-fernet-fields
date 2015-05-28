from cryptography.fernet import Fernet
from datetime import date, datetime

from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import connection, IntegrityError
from django.utils.encoding import force_bytes, force_text
import pytest

import fernet_fields as fields
from . import models


class TestEncryptedField(object):
    def test_key_from_settings(self, settings):
        """If present, use settings.FERNET_KEYS."""
        settings.FERNET_KEYS = ['secret']
        f = fields.EncryptedTextField()

        assert f.keys == settings.FERNET_KEYS

    def test_fallback_to_secret_key(self, settings):
        """If no FERNET_KEY setting, use SECRET_KEY."""
        f = fields.EncryptedTextField()

        assert f.keys == [settings.SECRET_KEY]

    def test_key_rotation(self, settings):
        """Can supply multiple `keys` for key rotation."""
        settings.FERNET_KEYS = ['key1', 'key2']
        f = fields.EncryptedTextField()

        enc1 = Fernet(f.fernet_keys[0]).encrypt(b'enc1')
        enc2 = Fernet(f.fernet_keys[1]).encrypt(b'enc2')

        assert f.fernet.decrypt(enc1) == b'enc1'
        assert f.fernet.decrypt(enc2) == b'enc2'

    def test_no_hkdf(self, settings):
        """Can set FERNET_USE_HKDF=False to avoid HKDF."""
        settings.FERNET_USE_HKDF = False
        k1 = Fernet.generate_key()
        settings.FERNET_KEYS = [k1]
        f = fields.EncryptedTextField()
        fernet = Fernet(k1)

        assert fernet.decrypt(f.fernet.encrypt(b'foo')) == b'foo'

    @pytest.mark.parametrize('key', ['primary_key', 'db_index', 'unique'])
    def test_not_allowed(self, key):
        with pytest.raises(ImproperlyConfigured):
            fields.EncryptedIntegerField(**{key: True})


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


class TestHashField(object):
    def test_deconstruct(self):
        f = fields.HashField('source')

        name, path, args, kwargs = f.deconstruct()

        assert args == ['source']


@pytest.mark.parametrize(
    'model,vals',
    [
        (models.HashText, ['foo', 'bar']),
        (models.HashNullable, [1, 2]),
    ],
)
class TestHashFieldQueries(object):
    def test_filter(self, db, model, vals):
        model.objects.create(value=vals[0])
        model.objects.create(value=vals[1])
        found = model.objects.get(hashed_value=vals[1])

        assert found.value == vals[1]


@pytest.mark.parametrize(
    'model',
    [models.DualUnique],
)
def test_unique(db, model):
    model.objects.create(value='foo')
    model.objects.create(value='bar')
    with pytest.raises(IntegrityError):
        model.objects.create(value='foo')


class TestDualField(object):
    @pytest.mark.parametrize('key', ['primary_key'])
    def test_not_allowed(self, key):
        with pytest.raises(ImproperlyConfigured):
            fields.DualIntegerField(**{key: True})

    def test_deconstruct(self):
        """Deconstruction prevents double-adding enc field in migrations."""
        f = fields.DualTextField()

        name, path, args, kwargs = f.deconstruct()

        assert not args
        assert kwargs['_add_encrypted_field'] is False


@pytest.mark.parametrize(
    'model,vals',
    [
        (models.DualText, ['foo', 'bar']),
        (models.DualChar, ['one', 'two']),
        (models.DualEmail, ['a@example.com', 'b@example.com']),
        (models.DualInt, [1, 2]),
        (models.DualDate, [date(2015, 2, 5), date(2015, 2, 8)]),
        (
            models.DualDateTime,
            [datetime(2015, 2, 5, 15), datetime(2015, 2, 8, 16)],
        ),
    ],
)
class TestDualFieldQueries(object):
    def test_insert(self, db, model, vals):
        """Data stored in DB is actually encrypted / hashed."""
        field = model._meta.get_field('value')
        enc_field = model._meta.get_field('value_encrypted')
        model.objects.create(value=vals[0])
        with connection.cursor() as cur:
            cur.execute(
                'SELECT value, value_encrypted FROM %s' % model._meta.db_table)
            values = []
            hashes = []
            for row in cur.fetchall():
                values.append(
                    force_text(enc_field.fernet.decrypt(force_bytes(row[1]))))
                hashes.append(force_bytes(row[0]))

        assert list(map(field.to_python, values)) == [vals[0]]
        assert hashes == [field.hash_value(vals[0])]

    def test_insert_and_select(self, db, model, vals):
        """Data round-trips through insert and select."""
        model.objects.create(value=vals[0])
        found = model.objects.get()

        assert found.value == vals[0]

    def test_update_and_select(self, db, model, vals):
        """Data round-trips through update and select."""
        model.objects.create(value=vals[0])
        model.objects.update(value=vals[1])
        found = model.objects.get(value=vals[1])

        assert found.value == vals[1]

    def test_double_update_and_select(self, db, model, vals):
        """Data round-trips through double update and select."""
        model.objects.create(value=vals[0])
        model.objects.update(value=vals[1])
        model.objects.update(value=vals[0])
        found = model.objects.get(value=vals[0])

        assert found.value == vals[0]

    def test_exact_lookup(self, db, model, vals):
        model.objects.create(value=vals[0])
        model.objects.create(value=vals[1])
        found = model.objects.get(value=vals[0])

        assert found.value == vals[0]

    def test_in_lookup(self, db, model, vals):
        model.objects.create(value=vals[0])
        model.objects.create(value=vals[1])
        found = model.objects.get(value__in=[vals[0]])

        assert found.value == vals[0]

    def test_other_lookups_raise_field_error(self, db, model, vals):
        model.objects.create(value=vals[0])

        with pytest.raises(FieldError):
            model.objects.get(value__gte=vals[0])


def test_update_other(db):
    models.DualPlus.objects.create(dual='one', other='two')
    models.DualPlus.objects.update(other='b')
    found = models.DualPlus.objects.get()

    assert found.other == 'b'


@pytest.mark.parametrize(
    'model',
    [models.EncryptedNullable, models.HashNullable, models.DualNullable],
)
def test_nullable(db, model):
    """Encrypted/dual/hash field can be nullable."""
    model.objects.create(value=None)
    found = model.objects.get()

    assert found.value is None
