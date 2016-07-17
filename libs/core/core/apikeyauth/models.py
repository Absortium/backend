from django.conf import settings
from django.db import models

from .constants import API_KEY_LEN, API_SECRETS_LEN
from .utils import generate_token

__author__ = 'andrew.shvv@gmail.com'


class Client(models.Model):
    api_key = models.CharField(max_length=API_KEY_LEN, default=generate_token)
    api_secret = models.CharField(max_length=API_SECRETS_LEN, default=generate_token)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="client")
