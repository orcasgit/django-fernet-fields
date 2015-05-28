from django.db import models

import fernet_fields as fields


class DualText(models.Model):
    value = fields.DualTextField(null=True)
