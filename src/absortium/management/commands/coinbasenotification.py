from pprint import pprint

from coinbase.wallet.client import Client
from django.conf import settings
from django.core.management.base import BaseCommand

from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)

__author__ = 'andrew.shvv@gmail.com'


class Command(BaseCommand):
    help = 'Get notification list form the coinbase'

    def handle(self, *args, **options):
        pprint(settings.COINBASE_API_KEY)
        pprint(settings.COINBASE_API_SECRET)

        client = Client(settings.COINBASE_API_KEY, settings.COINBASE_API_SECRET)
        notifications = client.get_notifications()

        pprint(notifications)
