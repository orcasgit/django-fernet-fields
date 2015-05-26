from django.apps.registry import Apps
from django.db import connection, models
import pytest

import fernet_fields as fields


app_registry = Apps()


class TestModel(models.Model):
    class Meta:
        abstract = True
        apps = app_registry
        app_label = 'backends'


@pytest.fixture
def Person(request):
    mark = request.keywords.get('fields', None)
    if mark is None:
        field_names = set(['name', 'age', 'email'])
    else:
        field_names = set(mark.args)

    class Person(TestModel):
        if 'name' in field_names:
            name = fields.EncryptedTextField()
        if 'age' in field_names:
            age = fields.EncryptedIntegerField(db_index=True)
        if 'email' in field_names:
            email = fields.EncryptedEmailField(unique=True)
        if 'jobs' in field_names:
            jobs = models.IntegerField(db_index=True)

    return Person


@pytest.mark.skipif(
    connection.vendor != 'postgresql', reason="indexes only work on PG")
@pytest.mark.django_db
class TestSchemaEditor(object):
    def get_indexes(self, model):
        """Get the indexes on a model's table.

        The primary key index on the `id` column will not be included, and an
        assertion error will be raised if there is any other PK index.

        Returns list of indexes including only (cols, unique).

        """
        indexes = []
        with connection.schema_editor() as editor:
            for name, cols, unique, pk in editor._get_indexes(model):
                if cols == ['id']:
                    continue
                assert not pk, "Unexpected PK index on %s" % cols
                indexes.append((cols, unique))
        return sorted(indexes)

    def test_single_column_indexes_on_table_create_remove(self, Person):
        with connection.schema_editor() as editor:
            editor.create_model(Person)
        indexes = self.get_indexes(Person)

        assert indexes == [
            (['"substring"(age, 1, 32)'], False),
            (['"substring"(email, 1, 32)'], True),
        ]

        with connection.schema_editor() as editor:
            editor.delete_model(Person)

        assert self.get_indexes(Person) == []

    @pytest.mark.fields('name')
    def test_add_db_index_to_field(self, Person):
        old_field = Person._meta.get_field('name')
        new_field = fields.EncryptedTextField(db_index=True)
        new_field.set_attributes_from_name('name')
        with connection.schema_editor() as editor:
            editor.create_model(Person)
        with connection.schema_editor() as editor:
            editor.alter_field(Person, old_field, new_field, strict=True)
        indexes = self.get_indexes(Person)

        assert indexes == [
            (['"substring"(name, 1, 32)'], False),
        ]

    @pytest.mark.fields('age')
    def test_remove_db_index_from_field(self, Person):
        old_field = Person._meta.get_field('age')
        new_field = fields.EncryptedIntegerField()
        new_field.set_attributes_from_name('age')
        with connection.schema_editor() as editor:
            editor.create_model(Person)
        with connection.schema_editor() as editor:
            editor.alter_field(Person, old_field, new_field, strict=True)
        indexes = self.get_indexes(Person)

        assert indexes == []

    @pytest.mark.fields('name')
    def test_add_unique_to_field(self, Person):
        old_field = Person._meta.get_field('name')
        new_field = fields.EncryptedTextField(unique=True)
        new_field.set_attributes_from_name('name')
        with connection.schema_editor() as editor:
            editor.create_model(Person)
        with connection.schema_editor() as editor:
            editor.alter_field(Person, old_field, new_field, strict=True)
        indexes = self.get_indexes(Person)

        assert indexes == [
            (['"substring"(name, 1, 32)'], True),
        ]

    @pytest.mark.fields('email')
    def test_remove_unique_from_field(self, Person):
        old_field = Person._meta.get_field('email')
        new_field = fields.EncryptedIntegerField()
        new_field.set_attributes_from_name('email')
        with connection.schema_editor() as editor:
            editor.create_model(Person)
        with connection.schema_editor() as editor:
            editor.alter_field(Person, old_field, new_field, strict=True)
        indexes = self.get_indexes(Person)

        assert indexes == []

    @pytest.mark.fields('age')
    def test_change_db_index_to_unique(self, Person):
        old_field = Person._meta.get_field('age')
        new_field = fields.EncryptedIntegerField(unique=True)
        new_field.set_attributes_from_name('age')
        with connection.schema_editor() as editor:
            editor.create_model(Person)
        with connection.schema_editor() as editor:
            editor.alter_field(Person, old_field, new_field, strict=True)
        indexes = self.get_indexes(Person)

        assert indexes == [
            (['"substring"(age, 1, 32)'], True),
        ]

    @pytest.mark.fields('email')
    def test_change_unique_to_db_index(self, Person):
        old_field = Person._meta.get_field('email')
        new_field = fields.EncryptedEmailField(db_index=True)
        new_field.set_attributes_from_name('email')
        with connection.schema_editor() as editor:
            editor.create_model(Person)
        with connection.schema_editor() as editor:
            editor.alter_field(Person, old_field, new_field, strict=True)
        indexes = self.get_indexes(Person)

        assert indexes == [
            (['"substring"(email, 1, 32)'], False),
        ]

    @pytest.mark.fields('jobs')
    def test_non_encrypted_db_index_still_works(self, Person):
        with connection.schema_editor() as editor:
            editor.create_model(Person)
        indexes = self.get_indexes(Person)

        assert indexes == [
            (['jobs'], False)
        ]

    @pytest.mark.fields('age')
    def test_remove_nonexistent_db_index_from_field(self, Person):
        old_field = Person._meta.get_field('age')
        new_field = fields.EncryptedIntegerField()
        new_field.set_attributes_from_name('age')
        with connection.schema_editor() as editor:
            editor.create_model(Person)
        with connection.schema_editor() as editor:
            editor.alter_field(Person, old_field, new_field, strict=True)
        with connection.schema_editor() as editor:
            editor.alter_field(Person, old_field, new_field, strict=True)
        indexes = self.get_indexes(Person)

        assert indexes == []
