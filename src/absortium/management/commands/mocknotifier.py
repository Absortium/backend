import time
from random import choice
from string import printable

import requests
from django.contrib.auth import settings
from django.core.management.base import BaseCommand, CommandError

from absortium import constants
from absortium.model.models import Account
from absortium.utils import convert
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)

__author__ = 'andrew.shvv@gmail.com'

TIMEDELTA = 20
DEFAULT_AMOUNT = convert(4)


def random_string(length=30):
    return "".join([choice(printable) for _ in range(length)])


class Command(BaseCommand):
    help = 'Send mock transaction notification to the backend'

    def handle(self, *args, **options):
        to_repr = {value: key for key, value in constants.AVAILABLE_CURRENCIES.items()}

        while True:
            accounts = Account.objects.all()
            for account in accounts:
                data = {
                    'tx_hash': random_string(),
                    'address': account.address,
                    'amount': DEFAULT_AMOUNT
                }

                if account.currency == constants.BTC:
                    token = settings.BTC_NOTIFICATION_TOKEN
                elif account.currency == constants.ETH:
                    token = settings.ETH_NOTIFICATION_TOKEN
                else:
                    raise CommandError("Could not match currency")

                url = 'http://docker.backend:3000/notifications/{currency}/{token}'.format(
                    currency=to_repr[account.currency],
                    token=token)
                response = requests.post(url, data)
                logger.debug(response.text)

            time.sleep(TIMEDELTA)
