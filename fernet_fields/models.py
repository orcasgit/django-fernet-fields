from django.db import models

from .queryset import DualManager


class DualModel(models.Model):
    class Meta:
        abstract = True

    objects = DualManager()
