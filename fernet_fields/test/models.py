from django.db import models

from fernet_fields import fields


class EncryptedText(models.Model):
    value = fields.EncryptedTextField(default='hey')


class EncryptedChar(models.Model):
    value = fields.EncryptedCharField(max_length=25)


class EncryptedEmail(models.Model):
    value = fields.EncryptedEmailField()


class EncryptedInt(models.Model):
    value = fields.EncryptedIntegerField(null=True)


class EncryptedDate(models.Model):
    value = fields.EncryptedDateField()


class EncryptedDateTime(models.Model):
    value = fields.EncryptedDateTimeField()


class EncryptedUnique(models.Model):
    value = fields.EncryptedTextField()
    hashed = fields.HashField('value', unique=True)


class EncryptedNullableHash(models.Model):
    value = fields.EncryptedTextField(null=True)
    hashed = fields.HashField('value', null=True)
