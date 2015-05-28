# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forwards(apps, schema_editor):
    DualText = apps.get_model('testmigrate', 'DualText')
    DualText.objects.create(value='foo')


def backwards(apps, schema_editor):
    DualText = apps.get_model('testmigrate', 'DualText')
    DualText.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('testmigrate', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
