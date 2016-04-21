__author__ = 'andrew.shvv@gmail.com'

from absortium import constants
from absortium.model.models import Exchange
from core.utils.logging import getLogger

from rest_framework.exceptions import ValidationError

logger = getLogger(__name__)


class LockedExchange():
    def __init__(self, exchange_pk):
        self.exchange_pk = exchange_pk

    def __enter__(self):
        #
        # if self.primary_exchange:
        #     c1 = self.primary_exchange.from_account == self.exchange.to_account
        #     c2 = self.primary_exchange.to_account == self.exchange.from_account
        #
        #     if c1 and c2:
        #         """
        #             If we process same accounts that means that we process opposite exchanges from the one user
        #             and we should not block accounts twice.
        #         """
        #
        #         self.exchange.from_account = self.primary_exchange.to_account
        #         self.exchange.to_account = self.primary_exchange.from_account
        #         return self.exchange

        # Init '[from|to]_account' in locking manner

        self.exchange = Exchange.objects.select_for_update().get(pk=self.exchange_pk)
        return self.exchange

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exchange.from_account.update(amount=self.exchange.from_account.amount)
        self.exchange.to_account.update(amount=self.exchange.to_account.amount)
        self.exchange.save()
