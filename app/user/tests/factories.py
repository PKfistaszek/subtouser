import random

import factory

from ..models import Client, User


def generate_phone_number(n):
    return "+48{}".format("".join([str(random.randint(1, 9)) for n in range(9)]))


class ClientFactory(factory.django.DjangoModelFactory):
    email = factory.Sequence(lambda n: "client_email_{}@test.pl".format(n))

    @factory.sequence
    def phone(n):
        return generate_phone_number(n)

    class Meta:
        model = Client


class UserFactory(factory.django.DjangoModelFactory):
    email = factory.Sequence(lambda n: "user_email_{}@test.pl".format(n))

    @factory.sequence
    def phone(n):
        return generate_phone_number(n)

    class Meta:
        model = User
