# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testmigrate', '0005_remove_old_value_field'),
    ]

    operations = [
        migrations.RenameField(
            'DualText', 'value_dual', 'value'),
        migrations.RenameField(
            'DualText', 'value_dual_encrypted', 'value_encrypted'),
    ]
