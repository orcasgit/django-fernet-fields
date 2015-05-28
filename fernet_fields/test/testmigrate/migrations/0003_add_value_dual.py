# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import fernet_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('testmigrate', '0002_add_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='dualtext',
            name='value_dual',
            field=fernet_fields.fields.DualTextField(
                null=True, _add_encrypted_field=False),
        ),
        migrations.AddField(
            model_name='dualtext',
            name='value_dual_encrypted',
            field=fernet_fields.fields.EncryptedTextField(
                null=True, editable=False),
        ),
    ]
