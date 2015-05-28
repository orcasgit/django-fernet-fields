# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testmigrate', '0004_copy_values'),
    ]

    operations = [
        migrations.RemoveField('DualText', 'value'),
    ]
