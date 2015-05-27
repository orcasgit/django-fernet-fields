from django.db import models

import fernet_fields as fields


class EncryptedText(models.Model):
    value = fields.EncryptedTextField()


class EncryptedChar(models.Model):
    value = fields.EncryptedCharField(max_length=25)


class EncryptedEmail(models.Model):
    value = fields.EncryptedEmailField()


class EncryptedInt(models.Model):
    value = fields.EncryptedIntegerField()


class EncryptedDate(models.Model):
    value = fields.EncryptedDateField()


class EncryptedDateTime(models.Model):
    value = fields.EncryptedDateTimeField()


class EncryptedNullable(models.Model):
    value = fields.EncryptedIntegerField(null=True)


class DualText(fields.DualModel):
    value = fields.DualTextField()


class DualChar(fields.DualModel):
    value = fields.DualCharField(max_length=25)


class DualEmail(fields.DualModel):
    value = fields.DualEmailField()


class DualInt(fields.DualModel):
    value = fields.DualIntegerField()


class DualDate(fields.DualModel):
    value = fields.DualDateField()


class DualDateTime(fields.DualModel):
    value = fields.DualDateTimeField()


class DualUnique(models.Model):
    value = fields.DualTextField(unique=True)


class DualNullable(models.Model):
    value = fields.DualTextField(null=True)
