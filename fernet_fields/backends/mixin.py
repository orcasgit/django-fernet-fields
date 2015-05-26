from collections import namedtuple
from contextlib import contextmanager

from django.db.backends.postgresql_psycopg2 import base


Index = namedtuple('Index', 'name, columns, unique, pk')


unset = object()


@contextmanager
def tempsetattr(obj, attr, val):
    """Context manager to set an attribute on an object and restore it."""
    orig = getattr(obj, attr, unset)
    setattr(obj, attr, val)
    try:
        yield
    finally:
        if orig is unset:
            delattr(obj, attr)
        else:
            setattr(obj, attr, orig)


@contextmanager
def noop(*args):
    yield


class DatabaseSchemaEditor(base.DatabaseSchemaEditor):
    # We can't use self.sql_create_unique, because that adds a unique
    # constraint rather than a unique index, and PostgreSQL doesn't allow
    # unique constraints on expressions. Unique indexes on expressions are
    # allowed and have the same effect as a constraint.
    sql_create_unique_index = (
        base.DatabaseSchemaEditor.sql_create_index.replace(
            'CREATE INDEX', 'CREATE UNIQUE INDEX')
    )
    sql_column_prefix = '"substring"(%s, 1, 32)'

    def _prehash(self, field):
        if getattr(field, 'prepend_hash', False):
            return 'unique' if field.unique else 'index'

    @contextmanager
    def _pretend_not(self, field, attr):
        """Context manager to temporarily set given field attr to False.

        Does nothing if field is not a prehash field.
        """
        cm = tempsetattr if self._prehash(field) else noop
        with cm(field, attr, False):
            yield

    def column_sql(self, model, field):
        # Avoid useless unique index on an entire encrypted column.
        with self._pretend_not(field, '_unique'):
            return super(DatabaseSchemaEditor, self).column_sql(model, field)

    def _create_index_sql(self, model, fields, *args, **kwargs):
        # This method is never called for unique indexes (because the base
        # schema editor expects those to be handled via table definition
        # instead), so we just handle non-unique indexes.
        if [self._prehash(f) for f in fields] == ['index']:
            return self._prefix_index_sql(model, fields[0])
        return super(
            DatabaseSchemaEditor, self
        )._create_index_sql(model, fields, *args, **kwargs)

    def _model_indexes_sql(self, model):
        """
        Return all index SQL statements (field indexes, index_together) for the
        specified model, as a list.
        """
        output = super(DatabaseSchemaEditor, self)._model_indexes_sql(model)
        # Non-unique indexes are handled in _create_index_sql, we just need to
        # tack on the unique hash-prefix indexes here.
        for field in model._meta.fields:
            if self._prehash(field) == 'unique':
                output.append(self._prefix_index_sql(model, field))
        return output

    def _alter_field(self, model, old_field, new_field, *args, **kwargs):
        # Pretend that neither old nor new field is unique, so we don't get a
        # unique index added to whole column, or errors when the super method
        # can't find the whole-column unique index it expects to.
        with self._pretend_not(new_field, '_unique'):
            with self._pretend_not(old_field, '_unique'):
                super(
                    DatabaseSchemaEditor, self
                )._alter_field(model, old_field, new_field, *args, **kwargs)
        old_idx = self._prehash(old_field)
        new_idx = self._prehash(new_field)
        idx_changed = (old_idx != new_idx)
        if old_idx and idx_changed:
            delete_sql = self._delete_prefix_index_sql(model, old_field)
            if delete_sql:
                self.execute(delete_sql)
        if new_idx == 'unique' and idx_changed:
            self.execute(self._prefix_index_sql(model, new_field))

    def _delete_prefix_index_sql(self, model, field):
        col = self.sql_column_prefix % field.column
        for idx in self._get_indexes(model):
            if col in idx.columns:
                return self.sql_delete_index % {'name': idx.name}

    def _prefix_index_sql(self, model, field):
        table = model._meta.db_table
        expr = self.sql_column_prefix % field.column
        suffix = '_prehash_uniq' if field.unique else '_prehash'
        template = (
            self.sql_create_unique_index
            if field.unique
            else self.sql_create_index
        )
        sql = template % {
            'table': table,
            'name': self._create_index_name(model, [field.column], suffix),
            'columns': expr,
            'extra': '',
        }
        return sql

    def _get_indexes(self, model):
        """Get the indexes on a model's table using a new cursor.

        Return list of indexes, where each index is a (name, columns, unique,
        pk) tuple, where ``name`` is the name of the index, ``columns`` is a
        list of the columns or expressions in the index, and ``unique`` and
        ``pk`` are booleans.

        """
        table = model._meta.db_table
        indexes = []
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                  ic.relname,
                  array(
                    SELECT pg_get_indexdef(
                      idx.indexrelid,
                      generate_subscripts(idx.indkey, 1) + 1,
                      false
                    )
                  ) AS columns,
                  idx.indisunique,
                  idx.indisprimary
                FROM
                  pg_catalog.pg_index idx,
                  pg_catalog.pg_class tc,
                  pg_catalog.pg_class ic
                WHERE tc.oid = idx.indrelid
                  AND ic.oid = idx.indexrelid
                  AND tc.relname = %s
                """, [table])
            for row in cursor.fetchall():
                indexes.append(Index(row[0], row[1], row[2], row[3]))
        return indexes


class PrefixIndexMixin(object):
    SchemaEditorClass = DatabaseSchemaEditor
