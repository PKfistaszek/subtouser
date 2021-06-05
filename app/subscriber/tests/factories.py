import factory

from user.tests.factories import generate_phone_number

from ..models import Subscriber, SubscriberSMS


class SubscriberFactory(factory.django.DjangoModelFactory):
    email = factory.Sequence(lambda n: "email_{}@test.pl".format(n))
    gdpr_consent = True

    class Meta:
        model = Subscriber


class SubscriberSMSFactory(factory.django.DjangoModelFactory):
    gdpr_consent = True

    @factory.sequence
    def phone(n):
        # TODO check is object with random phone number exists
        return generate_phone_number(n)

    class Meta:
        model = SubscriberSMS
