from django.db import models

from fernet_fields import fields


class EncryptedText(models.Model):
    value = fields.EncryptedTextField(default='hey', key='secret')


class EncryptedChar(models.Model):
    value = fields.EncryptedCharField(max_length=25, key='secret')


class EncryptedEmail(models.Model):
    value = fields.EncryptedEmailField(key='secret')


class EncryptedInt(models.Model):
    value = fields.EncryptedIntegerField(null=True, key='secret')


class EncryptedDate(models.Model):
    value = fields.EncryptedDateField(key='secret')


class EncryptedDateTime(models.Model):
    value = fields.EncryptedDateTimeField(key='secret')


class EncryptedUnique(models.Model):
    value = fields.EncryptedTextField(unique=True)
