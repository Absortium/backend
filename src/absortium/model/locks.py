__author__ = 'andrew.shvv@gmail.com'

from absortium.model.models import Exchange
from core.utils.logging import getLogger

logger = getLogger(__name__)


class LockedExchange():
    def __init__(self, exchange_pk, primary_exchange=None):
        self.exchange_pk = exchange_pk
        self.primary_exchange = primary_exchange

    def __enter__(self):
        self.exchange = Exchange.objects.select_for_update().get(pk=self.exchange_pk)

        if self.primary_exchange:

            if self.primary_exchange.owner_id == self.exchange.to_account.owner_id:
                # logger.debug("Same!! Exchange: {} {} => {}".format(self.primary_exchange.pk,
                #                                                    self.primary_exchange.from_account.pk,
                #                                                    self.primary_exchange.to_account.pk))
                """
                    If we process same accounts that means that we process opposite exchanges from the one user
                    and we should not block accounts twice.
                """

                self.exchange.from_account = self.primary_exchange.to_account
                self.exchange.to_account = self.primary_exchange.from_account
                return self.exchange

        # Init '[from|to]_account' in locking manner

        logger.debug("Lock exchange: {}".format(self.exchange_pk))

        return self.exchange

    def __exit__(self, exc_type, exc_val, exc_tb):
        # logger.debug(
        #     "Update account: {} amount {}".format(self.exchange.from_account.pk, self.exchange.from_account.amount))
        self.exchange.from_account.update(amount=self.exchange.from_account.amount)

        # logger.debug(
        #     "Update account: {} amount {}".format(self.exchange.to_account.pk, self.exchange.to_account.amount))
        self.exchange.to_account.update(amount=self.exchange.to_account.amount)
        self.exchange.save()
