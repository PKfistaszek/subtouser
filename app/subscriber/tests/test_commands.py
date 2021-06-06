from datetime import datetime, timedelta

from django.conf import settings
from django.core.management import call_command
from django.db import connection, reset_queries
from django.test import TestCase

from freezegun import freeze_time
from mock import Mock, patch

from user.models import User
from user.tests.factories import ClientFactory, UserFactory

from .factories import SubscriberFactory, SubscriberSMSFactory


class CommandsMigrateSubscriberToUserTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.DEBUG = True

    def setUp(self):
        super().setUp()
        self._subscribers = SubscriberFactory.create_batch(10)
        self._subscribers_sms = SubscriberSMSFactory.create_batch(10)
        reset_queries()

    def test_migrate_subscriber_and_subscribersms_to_empty_user(self):
        # Arrange
        expected_users_count = 20

        # Act

        call_command("migrate_subscriber_to_user")

        # Assert
        user_count = User.objects.count()
        self.assertEqual(user_count, expected_users_count)
        print(len(connection.queries))

    def test_user_with_the_same_email_like_subscriber_exists(self):
        """jeśli istnieje User z polem email takim samym jak w Subscriber
        - pomiń subskrybenta i nie twórz nowego użytkownika"""
        # Arrange
        first_subscriber = self._subscribers[0]
        expected_users_count = 20

        UserFactory(email=first_subscriber.email)

        # Act
        call_command("migrate_subscriber_to_user")

        # Assert
        user_count = User.objects.count()
        self.assertEqual(user_count, expected_users_count)
        print(len(connection.queries))

    def test_user_with_the_same_phone_like_subscriber_exists(self):
        """jeśli istnieje User z polem phone takim samym jak w Subscriber
        - pomiń subskrybenta i nie twórz nowego użytkownika"""
        # Arrange
        first_subscriber_sms = self._subscribers_sms[0]
        expected_users_count = 20

        UserFactory(phone=first_subscriber_sms.phone)

        # Act
        call_command("migrate_subscriber_to_user")

        # Assert
        user_count = User.objects.count()
        self.assertEqual(user_count, expected_users_count)
        print(len(connection.queries))

    def test_create_user_base_on_client_data_for_email(self):
        """
        jeśli istnieje Client z polem email takim jak Subscriber.email
        i nie istnieje User z polem phone takim jak Client.phone
        i polem email różnym od Client.email stwórz użytkownika
        na podstawie modelu Client
        """
        # Arrange
        first_subscriber = self._subscribers[0]

        client = ClientFactory.create(email=first_subscriber.email)

        # Act
        call_command("migrate_subscriber_to_user")

        # Assert
        self.assertTrue(
            User.objects.filter(
                email=client.email,
                phone=client.phone,
            ).exists()
        )
        self.assertEqual(User.objects.filter(gdpr_consent=True).count(), 19)
        print(len(connection.queries))

    def test_create_user_base_on_client_data_for_phone(self):
        """
        jeśli istnieje Client z polem phone takim jak Subscriber.phone
        i nie istnieje User z polem email takim jak Client.email
        i polem phone różnym od Client.phone stwórz użytkownika
        na podstawie modelu Client
        """
        # Arrange
        first_subscriber = self._subscribers_sms[0]

        client = ClientFactory.create(phone=first_subscriber.phone)

        # Act
        call_command("migrate_subscriber_to_user")

        # Assert
        self.assertTrue(
            User.objects.filter(
                email=client.email,
                phone=client.phone,
            ).exists()
        )
        self.assertEqual(User.objects.filter(gdpr_consent=True).count(), 19)
        print(len(connection.queries))

    @patch("subscriber.management.commands.migrate_subscriber_to_user.csv")
    def test_return_data_to_csv_if_two_clients_with_same_phone(self, csv):
        """
        jeśli istnieje 2 Clientów z polem phone takim jak Subscriber.phone
        i nie istnieje User z polem email takim jak Client.email
        i polem phone różnym od Client.phone stwórz użytkownika
        na podstawie modelu Client
        """
        # Arrange
        writer = Mock()
        csv.writer.return_value = writer

        first_subscriber = self._subscribers_sms[0]

        client = ClientFactory.create_batch(2, phone=first_subscriber.phone)[0]

        # Act
        call_command("migrate_subscriber_to_user")

        # Assert
        self.assertFalse(
            User.objects.filter(
                email=client.email,
                phone=client.phone,
            ).exists()
        )
        self.assertEqual(writer.writerow.call_count, 3)
        print(len(connection.queries))

    def test_not_create_user_base_on_client_data(self):
        """
        jeśli istnieje Client z polem email takim jak Subscriber.email
        i nie istnieje User z polem phone takim jak Client.phone
        i polem email takmim samym jak Client.email nie twórz użytkownika
        na podstawie modelu Client
        """
        # Arrange
        first_subscriber = self._subscribers[0]

        client = ClientFactory.create(email=first_subscriber.email)
        UserFactory.create(email=client.email)

        # Act
        call_command("migrate_subscriber_to_user")

        # Assert
        self.assertFalse(
            User.objects.filter(
                email=client.email,
                phone=client.phone,
            ).exists()
        )
        print(len(connection.queries))

    @patch("subscriber.management.commands.migrate_subscriber_to_user.csv")
    def test_return_data_to_csv_for_email(self, csv):
        """
        jeśli istnieje Client z polem email takim jak Subscriber.email
        i istnieje User z polem phone takim jak Client.phone i polem email
        różnym od Client.email zapisz id i email subskrybenta do pliku
        subscriber_conflicts.csv
        """
        # Arrange
        writer = Mock()
        csv.writer.return_value = writer

        first_subscriber = self._subscribers[0]

        client = ClientFactory.create(email=first_subscriber.email)
        UserFactory.create(phone=client.phone)

        # Act
        call_command("migrate_subscriber_to_user")

        # Assert
        self.assertEqual(writer.writerow.call_count, 3)
        print(len(connection.queries))

    @patch("subscriber.management.commands.migrate_subscriber_to_user.csv")
    def test_return_data_to_csv_for_phone(self, csv):
        """
        jeśli istnieje Client z polem phone takim jak Subscriber.phone
        i istnieje User z polem email takim jak Client.email i polem phone
        różnym od Client.phone zapisz id i phone subskrybenta do pliku
        subscriber_conflicts.csv
        """
        # Arrange
        writer = Mock()
        csv.writer.return_value = writer

        first_subscriber = self._subscribers_sms[0]

        client = ClientFactory.create(phone=first_subscriber.phone)
        UserFactory.create(email=client.email)

        # Act
        call_command("migrate_subscriber_to_user")

        # Assert
        self.assertEqual(writer.writerow.call_count, 3)
        print(len(connection.queries))

    @patch("subscriber.management.commands.migrate_subscriber_to_user.csv")
    def test_not_return_data_to_csv(self, csv):
        """
        jeśli istnieje Client z polem email takim jak Subscriber.email
        i istnieje User z polem phone takim jak Client.phone i polem email
        takim jak Client.email nie zapisuje id i email subskrybenta do pliku
        subscriber_conflicts.csv
        """
        # Arrange
        writer = Mock()
        csv.writer.return_value = writer

        first_subscriber = self._subscribers[0]

        client = ClientFactory.create(email=first_subscriber.email)
        UserFactory.create(phone=client.phone)
        UserFactory.create(email=client.email)

        # Act
        call_command("migrate_subscriber_to_user")

        # Assert
        self.assertEqual(writer.writerow._mock_call_count, 2)
        print(len(connection.queries))

    def test_create_user_with_empty_phone_number(self):
        """
        jeśli nie istnieje Client z polem email takim jak Subscriber.email, stwórz
        użytkownika z pustym polem phone
        """
        # Arrange

        first_subscriber = self._subscribers[0]

        UserFactory.create(email=first_subscriber.email, phone="")

        # Act
        call_command("migrate_subscriber_to_user")

        # Assert
        self.assertTrue(
            User.objects.filter(
                email=first_subscriber.email,
                phone="",
            ).exists()
        )
        print(len(connection.queries))


@freeze_time("2017-06-18")
class CommandsMigrateMissingDataFromSubscriberToUserTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.DEBUG = True

    def setUp(self):
        super().setUp()
        now = datetime.now()
        self.ONE_DAY_AGO = now - timedelta(days=1)
        self.WEEK_AGO = now - timedelta(days=7)
        self.MONTH_AGO = now - timedelta(days=30)

        # some extra data wich help with reduce the number o queries
        first_subscriber = SubscriberFactory.create_batch(10)[0]
        first_subscriber_sms = SubscriberSMSFactory.create_batch(10)[0]
        user = UserFactory(email=first_subscriber.email, gdpr_consent=False)
        user.created = self.MONTH_AGO
        user.save()
        user_2 = UserFactory(phone=first_subscriber_sms.phone, gdpr_consent=False)
        user_2.created = self.MONTH_AGO
        user_2.save()

        reset_queries()

    def test_migrate_subscriber_if_created_data_is_newer_then_user(self):
        # Arrange
        UserFactory.create_batch(5)
        subscriber = SubscriberFactory(gdpr_consent=True)
        user = UserFactory(email=subscriber.email, gdpr_consent=False)
        user.created = self.ONE_DAY_AGO
        user.save()

        reset_queries()
        # Act
        call_command("migrate_missing_data_from_subscriber_to_user")

        # Assert
        print(len(connection.queries))
        user.refresh_from_db()
        self.assertTrue(user.gdpr_consent)

    def test_migrate_subscriber_sms_if_created_data_is_newer_then_user(self):
        # Arrange
        UserFactory.create_batch(5)
        subscriber_sms = SubscriberSMSFactory(gdpr_consent=True)
        user = UserFactory(phone=subscriber_sms.phone, gdpr_consent=False)
        user.created = self.ONE_DAY_AGO
        user.save()

        reset_queries()
        # Act
        call_command("migrate_missing_data_from_subscriber_to_user")

        # Assert
        print(len(connection.queries))
        user.refresh_from_db()
        self.assertTrue(user.gdpr_consent)

    def test_migrate_subscriber_for_user_created_from_client_with_phone_and_email_subscriber_has_the_newer_date(self):  # noqa
        # Arrange
        UserFactory.create_batch(5)
        subscriber = SubscriberFactory(gdpr_consent=True)
        subscriber.created = self.ONE_DAY_AGO
        subscriber.save()

        subscriber_sms = SubscriberSMSFactory(gdpr_consent=False)
        subscriber_sms.created = self.WEEK_AGO
        subscriber_sms.save()

        user = UserFactory(
            email=subscriber.email, phone=subscriber_sms.phone, gdpr_consent=False
        )
        user.created = self.MONTH_AGO
        user.save()

        reset_queries()
        # Act
        call_command("migrate_missing_data_from_subscriber_to_user")

        # Assert
        print(len(connection.queries))
        user.refresh_from_db()
        self.assertTrue(user.gdpr_consent)

    def test_migrate_subscriber_for_user_created_from_client_with_phone_and_email_subscriber_sms_has_the_newer_date(self):  # noqa
        # Arrange
        UserFactory.create_batch(5)
        subscriber = SubscriberFactory(gdpr_consent=False)
        subscriber.created = self.WEEK_AGO
        subscriber.save()

        subscriber_sms = SubscriberSMSFactory(gdpr_consent=True)
        subscriber_sms.created = self.ONE_DAY_AGO
        subscriber_sms.save()

        user = UserFactory(
            email=subscriber.email, phone=subscriber_sms.phone, gdpr_consent=False
        )
        user.created = self.MONTH_AGO
        user.save()

        reset_queries()
        # Act
        call_command("migrate_missing_data_from_subscriber_to_user")

        # Assert
        print(len(connection.queries))
        user.refresh_from_db()
        self.assertTrue(user.gdpr_consent)

    def test_migrate_subscriber_for_user_created_from_client_with_phone_and_email_user_has_the_newer_date(self):  # noqa
        # Arrange
        UserFactory.create_batch(5)
        subscriber = SubscriberFactory(gdpr_consent=True)
        subscriber.created = self.WEEK_AGO
        subscriber.save()

        subscriber_sms = SubscriberSMSFactory(gdpr_consent=True)
        subscriber_sms.created = self.ONE_DAY_AGO
        subscriber_sms.save()

        user = UserFactory(
            email=subscriber.email, phone=subscriber_sms.phone, gdpr_consent=False
        )
        reset_queries()

        # Act
        call_command("migrate_missing_data_from_subscriber_to_user")

        # Assert
        print(len(connection.queries))
        user.refresh_from_db()
        self.assertFalse(user.gdpr_consent)
