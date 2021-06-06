from itertools import islice

from django.core.management.base import BaseCommand
from django.db.models import Q

from subscriber.models import Subscriber, SubscriberSMS
from user.models import User


BATCH_SIZE = 100


class Command(BaseCommand):
    help = """
    Command responsible for migrate missing data from subscribers to  User.
    """

    def handle(self, *args, **options):
        self._users_batch = []
        self._subscribers = Subscriber.objects.all()
        self._subscribers_sms = SubscriberSMS.objects.all()
        query_subscribers = Q(
            email__in=self._subscribers.values_list("email", flat=True)
        )
        query_subscribers_sms = Q(
            phone__in=self._subscribers_sms.values_list("phone", flat=True)
        )
        users = User.objects.filter(query_subscribers | query_subscribers_sms)
        self._prepare_users_for_update(users)
        self._users_batch = iter(self._users_batch)
        self._update_users()

    def _prepare_users_for_update(self, users):
        for user in users:
            subscriber = None
            subscriber_sms = None
            try:
                subscriber = self._subscribers.get(
                    email=user.email, created__gt=user.created
                )
            except Subscriber.DoesNotExist:
                pass
            try:
                subscriber_sms = self._subscribers_sms.get(
                    phone=user.phone, created__gt=user.created
                )
            except SubscriberSMS.DoesNotExist:
                pass
            if subscriber and subscriber_sms:
                if subscriber.created > subscriber_sms.created:
                    user.gdpr_consent = subscriber.gdpr_consent
                else:
                    user.gdpr_consent = subscriber_sms.gdpr_consent
            elif subscriber:
                user.gdpr_consent = subscriber.gdpr_consent
            elif subscriber_sms:
                user.gdpr_consent = subscriber_sms.gdpr_consent
            self._users_batch.append(user)

    def _update_users(self):
        if self._users_batch:
            while True:
                batch = list(islice(self._users_batch, BATCH_SIZE))
                if not batch:
                    break
                User.objects.bulk_update(batch, ["gdpr_consent"], BATCH_SIZE)
