from django.db.backends.postgresql_psycopg2 import base
from fernet_fields.backends.mixin import PrefixIndexMixin


class DatabaseWrapper(PrefixIndexMixin, base.DatabaseWrapper):
    pass
