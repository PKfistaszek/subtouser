from django.db import models


class AbstractTimeStampedModel(models.Model):
    """
    An abstract model responsible for self self updating created fields.
    """

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
