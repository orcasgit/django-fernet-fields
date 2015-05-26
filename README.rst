====================
django-fernet-fields
====================

.. image:: https://secure.travis-ci.org/orcasgit/django-fernet-fields.png?branch=master
   :target: http://travis-ci.org/orcasgit/django-fernet-fields
   :alt: Test status
.. image:: https://coveralls.io/repos/orcasgit/django-fernet-fields/badge.png?branch=master
   :target: https://coveralls.io/r/orcasgit/django-fernet-fields
   :alt: Test coverage
.. image:: https://pypip.in/v/django-fernet-fields/badge.png
   :target: https://pypi.python.org/pypi/django-fernet-fields
   :alt: Latest version
.. image:: https://pypip.in/license/django-fernet-fields/badge.png
   :target: https://pypi.python.org/pypi/django-fernet-fields
   :alt: License

`Fernet`_ symmetric encryption for Django model fields, using the
`cryptography`_ library.

``django-fernet-fields`` supports `Django`_ 1.8.2 and later on Python 2.7, 3.3,
3.4, pypy, and pypy3.

PostgreSQL is fully supported; SQLite is supported except for indexing and
unique constraints on encrypted fields. Support for other database backends
could easily be added (though indexing support is only possible on databases
that support indexes on expressions).

.. _Django: http://www.djangoproject.com/
.. _Fernet: https://cryptography.io/en/latest/fernet/
.. _cryptography: https://cryptography.io/en/latest/


Getting Help
============

Documentation for django-fernet-fields is available at
https://django-fernet-fields.readthedocs.org/

This app is available on `PyPI`_ and can be installed with ``pip install
django-fernet-fields``.

.. _PyPI: https://pypi.python.org/pypi/django-fernet-fields/


Contributing
============

See the `contributing docs`_.

.. _contributing docs: https://github.com/orcasgit/django-fernet-fields/blob/master/CONTRIBUTING.rst

