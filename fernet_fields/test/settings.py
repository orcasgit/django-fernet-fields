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

INSTALLED_APPS = [
    'fernet_fields.test'
]

SECRET_KEY = 'secret'

SILENCED_SYSTEM_CHECKS = ['1_7.W001']
