from .base import *  # noqa

import platform

if platform.python_implementation() == 'PyPy':
    from psycopg2cffi import compat
    compat.register()


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'djftest',
        'TEST': {
            'NAME': 'djftest',
        },
    },
}
