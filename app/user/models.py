from django.db import models

from phonenumber_field.modelfields import PhoneNumberField

from commons.models import AbstractTimeStampedModel


class User(AbstractTimeStampedModel):
    email = models.EmailField()
    phone = PhoneNumberField()
    gdpr_consent = models.BooleanField(default=False)


class Client(AbstractTimeStampedModel):
    email = models.EmailField(unique=True)
    phone = PhoneNumberField()
