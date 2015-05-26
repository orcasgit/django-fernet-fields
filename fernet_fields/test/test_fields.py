from cryptography.fernet import Fernet
from datetime import date, datetime

from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import connection, IntegrityError
from django.utils.encoding import force_bytes, force_text
import pytest

import fernet_fields as fields
from . import models


class TestEncryptedField(object):
    def test_deconstruct(self):
        f = fields.EncryptedTextField()

        assert f.deconstruct()[3] == {}

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

    def test_primary_key_not_allowed(self):
        with pytest.raises(ImproperlyConfigured):
            fields.EncryptedIntegerField(primary_key=True)


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


@pytest.mark.skipif(
    connection.vendor != 'postgresql', reason="indexes only work on PG")
class TestUniqueEncryptedField(object):
    def test_unique(self, db):
        """Encrypted field can enforce uniqueness."""
        models.EncryptedUnique.objects.create(value='foo')
        models.EncryptedUnique.objects.create(value='bar')

        with pytest.raises(IntegrityError):
            models.EncryptedUnique.objects.create(value='foo')


@pytest.mark.parametrize(
    'model', [models.EncryptedUnique, models.EncryptedIndex])
class TestIndexedLookups(object):
    def test_lookup_exact(self, db, model):
        """Can do an exact lookup on an indexed encrypted field."""
        model.objects.create(value='foo')
        model.objects.create(value='bar')
        found = model.objects.get(value='bar')

        assert found.value == 'bar'

    def test_lookup_in(self, db, model):
        """Can do an in lookup on an indexed encrypted field."""
        model.objects.create(value='foo')
        model.objects.create(value='bar')
        found = model.objects.get(value__in=['bar'])

        assert found.value == 'bar'

    @pytest.mark.skipif(
        connection.vendor != 'postgresql', reason="indexes only work on PG")
    def test_lookup_uses_index(self, db, model):
        """Exact lookup on indexed encrypted field uses index."""
        model.objects.create(value='foo')
        model.objects.create(value='bar')
        qs = model.objects.filter(value='bar')
        sql, params = qs.query.sql_with_params()
        with connection.cursor() as cur:
            cur.execute('EXPLAIN ' + sql, params)
            explanation = '\n'.join(r[0] for r in cur.fetchall())

        assert 'Index Scan' in explanation


def test_lookup_unsupported_vendor(db, monkeypatch):
    models.EncryptedUnique.objects.create(value='bar')
    monkeypatch.setattr(connection, 'vendor', 'foo')

    with pytest.raises(ImproperlyConfigured):
        models.EncryptedUnique.objects.get(value='bar')
