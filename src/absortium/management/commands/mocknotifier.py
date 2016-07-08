import json
import time
from random import choice
from string import printable

import requests
from django.contrib.auth import settings
from django.core.management.base import BaseCommand

from absortium import constants
from absortium.model.models import Account
from absortium.tests.utils import create_btc_notification, create_eth_notification
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)

__author__ = 'andrew.shvv@gmail.com'

TIMEDELTA = 20
DEFAULT_AMOUNT = 4


def random_string(length=30):
    return "".join([choice(printable) for _ in range(length)])


class Command(BaseCommand):
    help = 'Send mock transaction notification to the backend'

    def handle(self, *args, **options):
        to_repr = {value: key for key, value in constants.AVAILABLE_CURRENCIES}

        while True:
            accounts = Account.objects.filter(owner__isnull=False).all()

            for account in accounts:
                amount = DEFAULT_AMOUNT
                address = account.address

                if account.currency == constants.BTC:
                    token = settings.BTC_NOTIFICATION_TOKEN
                    data = create_btc_notification(address=address,
                                                   amount=amount)
                    logger.debug(data)

                elif account.currency == constants.ETH:
                    token = settings.ETH_NOTIFICATION_TOKEN
                    data = create_eth_notification(address=address,
                                                   amount=amount)
                    logger.debug(data)
                else:
                    raise Exception("Unknown currency")

                url = 'http://docker.backend:3000/notifications/{token}'.format(token=token)
                response = requests.post(url, json=data)
                logger.debug(response.text)

            time.sleep(TIMEDELTA)
