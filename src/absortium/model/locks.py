__author__ = 'andrew.shvv@gmail.com'

from absortium.model.models import Account, Exchange
from core.utils.logging import getLogger

logger = getLogger(__name__)


class LockedExchange():
    def __init__(self, exchange_pk):
        self.exchange = Exchange.objects.select_for_update().get(pk=exchange_pk)
        # self.primary_exchange = primary_exchange

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
        self.exchange.from_account = Account.objects.select_for_update().get(pk=self.exchange.from_account_id)
        self.exchange.to_account = Account.objects.select_for_update().get(pk=self.exchange.to_account_id)
        return self.exchange

    def __exit__(self, exc_type, exc_val, exc_tb):
        from_pk = self.exchange.from_account.pk
        to_pk = self.exchange.to_account.pk

        Account.objects.filter(pk=from_pk).update(amount=self.exchange.from_account.amount)
        Account.objects.filter(pk=to_pk).update(amount=self.exchange.to_account.amount)

        self.exchange.save()


class LockWithdrawal():
    pass
