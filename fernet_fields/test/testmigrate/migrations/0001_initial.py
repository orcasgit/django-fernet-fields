# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DualText',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ('value', models.TextField(null=True)),
            ],
        ),
    ]
