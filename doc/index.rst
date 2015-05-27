Welcome to django-fernet-fields!
================================

`Fernet`_ symmetric encryption for Django model fields, using the
`cryptography`_ library.

.. _Fernet: https://cryptography.io/en/latest/fernet/
.. _cryptography: https://cryptography.io/en/latest/


Prerequisites
-------------

``django-fernet-fields`` supports `Django`_ 1.8.2 and later on Python 2.7, 3.3,
3.4, pypy, and pypy3.

Only PostgreSQL, SQLite, and MySQL are tested, but any Django database backend
with support for ``BinaryField`` should work.

.. _Django: http://www.djangoproject.com/


Installation
------------

``django-fernet-fields`` is available on `PyPI`_. Install it with::

    pip install django-fernet-fields

.. _PyPI: https://pypi.python.org/pypi/django-fernet-fields/


Usage
-----

Just import and use the included field classes in your models::

    from django.db import models
    from fernet_fields import EncryptedTextField


    class MyModel(models.Model):
        name = EncryptedTextField()

You can assign values to and read values from the ``name`` field as usual, but
the values will automatically be encrypted before being sent to the database
and decrypted when read from the database.

Encryption and decryption are performed in your app; the secret key is never
sent to the database server. The database sees only the encrypted values of
this field.


Field types
~~~~~~~~~~~

Several other field classes are included: ``EncryptedCharField``,
``EncryptedEmailField``, ``EncryptedIntegerField``, ``EncryptedDateField``, and
``EncryptedDateTimeField``. All field classes accept the same arguments as
their non-encrypted versions (in addition to the optional encryption-specific
keyword arguments discussed below).

To create an encrypted version of some other custom field class, inherit from
both ``EncryptedField`` and the other field class::

    from fernet_fields import EncryptedField
    from somewhere import MyField

    class MyEncryptedField(EncryptedField, MyField):
        pass


Keys
----

By default, ``django-fernet-fields`` uses your ``SECRET_KEY`` setting as the
encryption key.

You can instead provide a list of keys in the ``FERNET_KEYS`` setting; the
first key will be used to encrypt all new data, and decryption of existing
values will be attempted with all given keys in order. This is useful for key
rotation: place a new key at the head of the list for use with all new or
changed data, but existing values encrypted with old keys will still be
accessible::

    FERNET_KEYS = [
        'new key for encrypting',
        'older key for decrypting old data',
    ]

.. warning::

   Once you start saving data using a given encryption key (whether your
   ``SECRET_KEY`` or another key), don't lose track of that key or you will
   lose access to all data encrypted using it! And keep the key secret; anyone
   who gets ahold of it will have access to all your encrypted data.


Disabling HKDF
~~~~~~~~~~~~~~

Fernet encryption requires a 32-bit url-safe base-64 encoded secret key. By
default, ``django-fernet-fields`` uses `HKDF`_ to derive such a key from
whatever arbitrary secret key you provide.

If you wish to disable HKDF and provide your own Fernet-compatible 32-bit
key(s) (e.g. generated with `Fernet.generate_key()`_) directly instead, just
set ``FERNET_USE_HKDF = False`` in your settings file. If this is set, all keys
passed to encrypted fields directly or specified in the ``FERNET_KEYS`` setting
must be 32-bit and url-safe base64-encoded bytestrings. If a key is not in the
correct format, you'll likely get "incorrect padding" errors.

.. warning::

   If you don't define a ``FERNET_KEYS`` setting, your ``SECRET_KEY`` setting
   is the fallback key. If you disable HKDF, this means that your
   ``SECRET_KEY`` itself needs to be a Fernet-compatible key.

.. _HKDF: https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#cryptography.hazmat.primitives.kdf.hkdf.HKDF
.. _Fernet.generate_key(): https://cryptography.io/en/latest/fernet/#cryptography.fernet.Fernet.generate_key


Indexes, constraints, and lookups
---------------------------------

Because Fernet encryption is not deterministic (the same source text encrypted
using the same key will result in a different encrypted token each time),
indexing or enforcing uniqueness or performing lookups against encrypted data
is useless. Every encrypted value will always be different, and every
exact-match lookup will fail; some other lookup types could appear to succeed,
but the results would be meaningless.

For this reason, and to avoid unexpected surprises, ``EncryptedField`` will
raise ``django.core.exceptions.ImproperlyConfigured`` if passed any of
``db_index=True``, ``unique=True``, or ``primary_key=True``, and any type of
lookup on an ``EncryptedField`` will raise
``django.core.exceptions.FieldError``.

If you need to allow indexes and exact-match lookups against encrypted fields,
use a ``DualField`` instead:


DualField
---------

In order to allow exact-match lookups and indexing (including unique
constraints) of encrypted fields, a ``DualField`` stores two columns in the
database: one with a SHA-256 hash of the source value, and one with the
Fernet-encrypted value.

The SHA-256 hash is not reversible (that is, the original value can't be
recovered from the hash), but it is deterministic (the same source value will
always have the same hash), so it can be used for indexing, unique constraints,
and lookups.

The Fernet-encrypted value is used only to recover the original data when
querying the database.

The same six ``DualField`` subclasses are included: ``DualTextField``,
``DualCharField``, ``DualEmailField``, ``DualIntegerField``, ``DualDateField``,
and ``DualDateTimeField``. Use them as you would any other field::

    from django.db import models
    from fernet_fields import DualEmailField


    class MyModel(models.Model):
        email = DualEmailField(unique=True)

Unlike ``EncryptedField``, ``DualField`` supports ``db_index=True`` and
``unique=True`` (still no ``primary_key=True``, though). Exact-match, ``__in``,
and ``__isnull`` lookups are also permitted.

Encryption keys are handled in the same way as for ``EncryptedField``.

.. warning::

   Because the SHA-256 hash is non-reversible, ``DualField`` still protects
   your data in case of a database compromise. However, you do expose a bit
   more information with ``DualField`` due to the deterministic hash. An
   attacker can now see which rows have the same values and which have
   different values (which an ``EncryptedField`` alone would not expose).

   For this reason (and for simplicity of implementation) I recommend using
   ``EncryptedField`` whenever possible, and only using ``DualField`` when you
   absolutely need lookups and/or a database-level unique constraint on an
   encrypted field.


Enabling updates
~~~~~~~~~~~~~~~~

Due to limitations of the Django ORM, Django's default ``QuerySet.update()``
does not work correctly if a ``DualField`` is updated; the hashed value is
updated (so lookups will see the new value) but the encrypted value is not.

In order to enable ``QuerySet.update()`` on a ``DualField``, you must use
``fernet_fields.DualQuerySet`` instead. A ``DualManager`` is provided which
uses ``DualQuerySet``::

    from django.db import models
    import fernet_fields

    class MyModel(models.Model):
        email = fernet_fields.DualEmailField()

        objects = fernet_fields.DualManager()

For this simplest case (where you only want one default manager on your class,
named ``objects``), you can instead just inherit from the ``DualModel`` base
model class (which does nothing but add ``objects = DualManager()``)::

    from django.db import models
    import fernet_fields
    from fernet_fields.models import DualModel

    class MyModel(DualModel):
        email = fernet_fields.DualEmailField()

This is equivalent to the above snippet using ``DualManager`` explicitly.

If you already have a custom ``Manager`` subclass, you can create a manager
that uses ``DualQuerySet`` via ``Manager.from_queryset()``::

    from django.db import models
    import fernet_fields
    from somewhere import MyManager

    MyDualManager = MyManager.from_queryset(fernet_fields.DualQuerySet)

    class MyModel(models.Model):
        email = fernet_fields.DualEmailField()

        objects = MyDualManager()


Ordering
--------

Ordering a queryset by an ``EncryptedField`` or ``DualField`` will appear to
work, but it will order according to the encrypted (or hashed) data, not the
decrypted value, which is not very useful and probably not desired.


Migrations
----------

If migrating an existing non-encrypted field to its encrypted (or dual)
counterpart, you won't be able to use a simple ``AlterField`` operation. Since
your database has no access to the encryption key, it can't update the column
values correctly. Instead, you'll need to do a three-step migration dance:

1. Add the new encrypted field with a different name.
2. Write a data migration (using RunPython and the ORM, not raw SQL) to copy
   the values from the old field to the new (which automatically encrypts them
   in the process).
3. Remove the old field and (if needed) rename the new encrypted field to the
   old field's name.

The same applies to migrating from an ``EncryptedField`` to a ``DualField`` or
vice versa.


Contributing
------------

See the `contributing docs`_.

.. _contributing docs: https://github.com/orcasgit/django-fernet-fields/blob/master/CONTRIBUTING.rst
