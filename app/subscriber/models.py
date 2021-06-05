from django.db import models

from phonenumber_field.modelfields import PhoneNumberField

from commons.models import AbstractTimeStampedModel


class AbstractSubscriber(AbstractTimeStampedModel):
    gdpr_consent = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Subscriber(AbstractSubscriber):
    email = models.EmailField(unique=True)


class SubscriberSMS(AbstractSubscriber):
    phone = PhoneNumberField(unique=True)
