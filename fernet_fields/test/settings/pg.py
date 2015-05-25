from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'djftest',
        'TEST': {
            'NAME': 'djftest',
        },
    },
}
