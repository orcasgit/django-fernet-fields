from django.db.backends.postgresql_psycopg2 import base


class DatabaseSchemaEditor(base.DatabaseSchemaEditor):
    # We can't use self.sql_create_unique, because that adds a unique
    # constraint rather than a unique index, and PostgreSQL doesn't allow
    # unique constraints on expressions. Unique indexes on expressions are
    # allowed and have the same effect as a constraint.
    sql_create_unique_index = (
        base.DatabaseSchemaEditor.sql_create_index.replace(
            'CREATE INDEX', 'CREATE UNIQUE INDEX')
    )

    def _model_indexes_sql(self, model):
        """
        Return all index SQL statements (field indexes, index_together) for the
        specified model, as a list.
        """
        output = super(DatabaseSchemaEditor, self)._model_indexes_sql(model)
        for field in model._meta.fields:
            if getattr(field, 'prepend_hash', None):
                output.extend(self._prefix_indexes_sql(model, field))
        return output

    def _prefix_sql(self, prefix_len):
        return 'SUBSTRING(%%s for %s)' % prefix_len

    def _prefix_indexes_sql(self, model, field):
        output = []
        table = model._meta.db_table
        unique = field.prepend_hash == 'unique'
        expr = self._prefix_sql(32) % field.column
        suffix = '_prehash_uniq' if unique else '_prehash'
        template = (
            self.sql_create_unique_index
            if unique
            else self.sql_create_index
        )
        sql = template % {
            'table': table,
            'name': self._create_index_name(model, [field.column], suffix),
            'columns': expr,
            'extra': '',
        }
        output.append(sql)
        return output


class PrefixIndexMixin(object):
    SchemaEditorClass = DatabaseSchemaEditor
