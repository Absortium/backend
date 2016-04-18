__author__ = 'andrew.shvv@gmail.com'

from absortium import constants
from absortium.model.models import Account, Exchange

from core.utils.logging import getLogger

logger = getLogger(__name__)


class NotEnoughMoney(Exception):
    msg = "Not enought money"


class ExchangeLock():
    def __init__(self, exchange_pk):
        self.exchange = Exchange.objects.select_for_update().get(pk=exchange_pk)

    def __enter__(self):
        # Init '[from|to]_account' in locking manner
        self.exchange.from_account = Account.objects.select_for_update().get(pk=self.exchange.from_account_id)
        self.exchange.to_account = Account.objects.select_for_update().get(pk=self.exchange.to_account_id)
        return self.exchange

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.exchange.status != constants.EXCHANGE_REJECTED:
            Account.objects.filter(pk=self.exchange.from_account.pk).update(amount=self.exchange.from_account.amount)
            Account.objects.filter(pk=self.exchange.to_account.pk).update(amount=self.exchange.to_account.amount)
            self.exchange.save()
        else:
            self.exchange.delete()
