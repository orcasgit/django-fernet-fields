from cryptography.fernet import Fernet
from django.db import models

from fernet_fields import fields


TEST_KEY = Fernet.generate_key()


fernet = Fernet(TEST_KEY)


class EncryptedText(models.Model):
    value = fields.EncryptedTextField(default='hey', key=TEST_KEY)


class EncryptedChar(models.Model):
    value = fields.EncryptedCharField(max_length=25, key=TEST_KEY)


class EncryptedEmail(models.Model):
    value = fields.EncryptedEmailField(key=TEST_KEY)


class EncryptedInt(models.Model):
    value = fields.EncryptedIntegerField(null=True, key=TEST_KEY)


class EncryptedDate(models.Model):
    value = fields.EncryptedDateField(key=TEST_KEY)


class EncryptedDateTime(models.Model):
    value = fields.EncryptedDateTimeField(key=TEST_KEY)
