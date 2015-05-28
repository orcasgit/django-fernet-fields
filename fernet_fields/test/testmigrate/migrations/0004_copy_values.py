# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forwards(apps, schema_editor):
    DualText = apps.get_model('testmigrate', 'DualText')
    for obj in DualText.objects.all():
        obj.value_dual = obj.value


def backwards(apps, schema_editor):
    DualText = apps.get_model('testmigrate', 'DualText')
    for obj in DualText.objects.all():
        obj.value = obj.value_dual


class Migration(migrations.Migration):

    dependencies = [
        ('testmigrate', '0003_add_value_dual'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
