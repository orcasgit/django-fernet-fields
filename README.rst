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

Django model fields whose value is transparently encrypted using the `Fernet
recipe`_ from the `cryptography`_ library.

``django-fernet-fields`` supports `Django`_ 1.8.2 and later on Python 2.7, 3.3,
3.4, pypy, and pypy3. Currently PostgreSQL and SQLite are the only supported
databases, but support for other backends could easily be added.

.. _Django: http://www.djangoproject.com/
.. _Fernet recipe: https://cryptography.io/en/latest/fernet/
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

