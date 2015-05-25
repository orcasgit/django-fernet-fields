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

PostgreSQL is currently the only database with built-in support; support for
other database backends should be easy to add.

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

To create an encrypted version of some other custom field class, use
``EncryptedFieldMixin``::

    from fernet_fields import EncryptedFieldMixin
    from somewhere import MyField

    class MyEncryptedField(EncryptedFieldMixin, MyField):
        pass


Caveats
-------

Indexes, constraints and lookups
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because Fernet encryption is not deterministic (the same source text encrypted
using the same key will result in a different encrypted token each time),
indexing or enforcing uniqueness or performing lookups against encrypted
columns is useless. Every value in the column will always be different, and
every exact-match lookup will fail; some other lookup types could seem to
succeed, but the results would be meaningless.

For this reason and to prevent surprising behavior, all encrypted fields will
raise ``django.core.exceptions.ImproperlyConfigured`` if they receive any of
``primary_key=True``, ``unique=True``, or ``db_index=True``, and will raise
``django.core.exceptions.FieldError`` if they are used in a lookup (e.g. a call
to ``QuerySet.filter()`` and friends).


Migrations
~~~~~~~~~~

If migrating an existing non-encrypted field to its encrypted counterpart, you
won't be able to use an ``AlterField`` operation. Since your database has no
access to the encryption key, it can't update the column values
correctly. Instead, you'll need to do a three-step migration dance:

1. Add the new encrypted field with a different name.
2. Write a data migration to copy the values from the old field to the new.
3. Remove the old field and (if needed) rename the new encrypted field to the
   old field's name.


Keys
----

By default, ``django-fernet-fields`` uses your ``SECRET_KEY`` setting as the
encryption key.

You can specify a different key per encrypted field by passing the ``key``
argument to an encrypted field::

    class MyModel(models.Model):
        name = EncryptedTextField(key='some long and random secret value')

.. warning::

   Once you start saving data using a given encryption key (whether your
   ``SECRET_KEY`` or another key), don't lose track of that key or you will
   lose access to all data encrypted using it! And keep the key secret; anyone
   who gets ahold of it will have access to all your encrypted data.


Key rotation
~~~~~~~~~~~~

You can instead provide a list of keys using the ``keys`` argument; the first
key will be used to encrypt all new data, and decryption of existing values
will be attempted with all given keys in order. This is useful for key
rotation: place a new key at the head of the list for use with all new or
changed data, but existing values encrypted with old keys will still be
accessible::

    class MyModel(models.Model):
        name = EncryptedTextField(keys=['new key', 'older key'])

You can also set the ``FERNET_KEYS`` setting to a list of keys, which will be
used as the default for any encrypted field that does not receive a ``key`` or
``keys`` argument.


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

   If you don't define a ``FERNET_KEYS`` setting or pass key(s) explicitly to
   every encrypted field, your ``SECRET_KEY`` setting is the fallback key. If
   you disable HKDF, this means that your ``SECRET_KEY`` itself needs to be a
   Fernet-compatible key.

You can also disable HKDF per-encrypted-field by passing the ``use_hkdf=False``
keyword argument.

.. _HKDF: https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#cryptography.hazmat.primitives.kdf.hkdf.HKDF
.. _Fernet.generate_key(): https://cryptography.io/en/latest/fernet/#cryptography.fernet.Fernet.generate_key
