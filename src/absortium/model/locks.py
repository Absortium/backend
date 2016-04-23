__author__ = 'andrew.shvv@gmail.com'

from django.db.utils import OperationalError

from absortium.model.models import Exchange, Account
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


import decimal
from absortium import constants


class GetLockedOpposite():
    def __init__(self, exchange=None):
        self.exchange = exchange

    def __enter__(self):
        converted_price = decimal.Decimal("1.0") / self.exchange.price

        self.opposite = Exchange.objects.filter(
            status=constants.EXCHANGE_PENDING,
            price__lte=converted_price,
            from_currency=self.exchange.to_currency)[0]

        if self.exchange.owner_id == self.opposite.to_account.owner_id:
            """
                If we process same accounts that means that we process opposite exchanges from the one user
                and we should not block accounts twice.
            """

            self.opposite.from_account = self.exchange.to_account
            self.opposite.to_account = self.exchange.from_account

        return self.opposite

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.opposite.from_account.update(amount=self.exchange.from_account.amount)
        self.opposite.to_account.update(amount=self.exchange.to_account.amount)
        self.opposite.save()


class lockexchange:
    def __init__(self, exchange=None):
        self.exchange = exchange

    def __enter__(self):
        if not self.exchange.from_account and not self.exchange.to_account:
            """
                Such strange select was done in order to prevent deadlock.

                Thread #1 (Exchange #1)             Thread #2 (Exchange #2) - opposite exchange
                Lock ETC account (from_account)
                                                    Lock BTC account (from_account)

                Lock BTC account (to_account) <--- lock because BTC account was already locked

                                                    Lock ETC account (to_account) <--- dead lock

            """
            accounts = Account.objects.select_for_update().filter(owner__pk=self.exchange.owner_id,
                                                                  currency__in=[self.exchange.from_currency,
                                                                                self.exchange.to_currency])
            for account in accounts:
                if account.currency == self.exchange.from_currency:
                    self.exchange.from_account = account
                if account.currency == self.exchange.to_currency:
                    self.exchange.to_account = account

        return self.exchange

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exchange.from_account.update(amount=self.exchange.from_account.amount)
        self.exchange.to_account.update(amount=self.exchange.to_account.amount)
        self.exchange.save()


class opposites:
    def __init__(self, exchange):
        self.exchange = exchange
        self.converted_price = decimal.Decimal("1.0") / self.exchange.price

    def __iter__(self):
        return self

    def __next__(self):
        try:
            opposite = None
            i = 0
            while not opposite:
                try:
                    opposite = Exchange.objects.select_for_update(nowait=False).filter(
                        status=constants.EXCHANGE_PENDING,
                        price__lte=self.converted_price,
                        from_currency=self.exchange.to_currency)[i]
                except OperationalError:
                    i += 1

            if self.exchange.owner_id == opposite.owner_id:
                """
                    If we process same accounts that means that we process opposite exchanges from the one user
                    and we should not block accounts twice.
                """
                opposite.from_account = self.exchange.to_account
                opposite.to_account = self.exchange.from_account

        except IndexError:
            raise StopIteration()
        else:
            return opposite
