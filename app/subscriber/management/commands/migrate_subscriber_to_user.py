import csv
from itertools import islice

from django.core.management.base import BaseCommand
from django.db.models import Q

from subscriber.models import Subscriber, SubscriberSMS
from user.models import Client, User


BATCH_SIZE = 100


class Command(BaseCommand):
    help = "Command responsible for migrate data from subscribers to User."

    def handle(self, *args, **options):
        self._users_batch = []
        models_with_params = [
            {
                "model": Subscriber,
                "fields": {"field_to_migrate": "email", "field_to_check": "phone"},
            },
            {
                "model": SubscriberSMS,
                "fields": {
                    "field_to_migrate": "phone",
                    "field_to_check": "email",
                },
            },
        ]
        self._prepare_users_for_migration(models_with_params)
        self._users_batch = iter(self._users_batch)
        self._create_users()

    def _prepare_users_for_migration(self, models_with_params):
        for data in models_with_params:
            model = data["model"]
            field_to_migrate = data["fields"]["field_to_migrate"]
            subscribers = data[
                "model"
            ].objects.all()  # probaly I should thing over also chunk the subscribers  # noqa
            file_name = f"{model.__name__}_conflicts.csv"

            with open(file_name.lower(), "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["ID", field_to_migrate.upper()])
                filter_attr = {
                    f"{field_to_migrate}__in": [
                        getattr(subscriber, field_to_migrate)
                        for subscriber in subscribers
                    ]
                }
                skip_values = User.objects.filter(**filter_attr).values_list(
                    field_to_migrate, flat=True
                )
                subscribers = subscribers.exclude(
                    **{f"{field_to_migrate}__in": skip_values}
                )
                for subscriber in subscribers:
                    self._check_data_in_clients(subscriber, writer, data["fields"])

    def _check_data_in_clients(self, subscriber, writer, fields):
        field_to_migrate = fields["field_to_migrate"]
        field_to_check = fields["field_to_check"]

        # should be impletmented in this way to reduce the number of queries
        # clients = Client.objects.filter(
        #     **{f'{field_to_migrate}__in': [
        #         getattr(subscriber, field_to_migrate)
        #         for subscriber in subscribers
        #     ]}
        # )
        try:
            client = Client.objects.get(
                **{field_to_migrate: getattr(subscriber, field_to_migrate)}
            )
            query_1 = Q(**{field_to_check: getattr(client, field_to_check)})
            query_2 = Q(**{field_to_migrate: getattr(client, field_to_migrate)})
            if User.objects.filter(query_1 & ~query_2).exists():
                writer.writerow([subscriber.id, getattr(subscriber, field_to_migrate)])
            elif not User.objects.filter(query_1 & ~query_2).exists():
                user = User(
                    email=client.email,
                    phone=client.phone,
                )
                self._users_batch.append(user)
        except Client.DoesNotExist:
            user = User(
                email=getattr(subscriber, field_to_migrate),
                gdpr_consent=subscriber.gdpr_consent,
            )
            self._users_batch.append(user)
        except Client.MultipleObjectsReturned:
            writer.writerow([subscriber.id, getattr(subscriber, field_to_migrate)])

    def _create_users(self):
        if self._users_batch:
            while True:
                batch = list(islice(self._users_batch, BATCH_SIZE))
                if not batch:
                    break
                User.objects.bulk_create(batch, BATCH_SIZE)
