__author__ = 'andrew.shvv@gmail.com'

from django.conf import settings
from django.db import models


class Social(models.Model):
    provider = models.CharField(max_length=10)
    provider_uid = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    class Meta:
        app_label = 'jwtauth'
        unique_together = ("provider_uid", "provider")
