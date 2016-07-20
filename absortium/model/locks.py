from absortium import constants
from absortium.model import models
from core.utils.logging import getLogger

__author__ = 'andrew.shvv@gmail.com'

logger = getLogger(__name__)


class lockaccounts:
    def __init__(self, order=None):
        self.order = order
        self.status = order.status
        self.amount = order.amount
        self.price = order.price
        self.total = order.total

        if order.pk is None:
            self.order.save()

    def __enter__(self):
        if not self.order.from_account and not self.order.to_account:
            """
                Such strange select was done in order to prevent deadlocks (we should lock two accounts at one atomic operation).
                Example:

                Thread #1 (Order #1)             Thread #2 (Order #2) - opposite order
                Lock ETC account (from_account)
                                                    Lock BTC account (from_account)

                Lock BTC account (to_account) <---'lock' because BTC account was already locked

                                                    Lock ETC account (to_account) <--- dead lock

            """

            accounts = models.Account.locks(owner__pk=self.order.owner_id,
                                            currency__in=[self.order.primary_currency,
                                                          self.order.secondary_currency])

            for account in accounts:
                if account.currency == self.order.from_currency:
                    self.order.from_account = account
                if account.currency == self.order.to_currency:
                    self.order.to_account = account

        return self.order

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_val:
            """
                Account always should be updated even if order in 'init' state, because we subtract order amount from account.
            """
            models.Account.update(pk=self.order.from_account.pk, amount=self.order.from_account.amount)
            models.Account.update(pk=self.order.to_account.pk, amount=self.order.to_account.amount)

            c1 = self.status != self.order.status
            c2 = self.amount != self.order.amount
            c3 = self.price != self.order.price
            c4 = self.total != self.order.total

            if c1 or c2 or c3 or c4:
                self.order.save()


class get_opposites:
    """
        1. Search for opposite orders.
        2. Block order with pg_try_advisory_xact_lock postgres lock.
    """

    def __init__(self, order):
        self.order = order
        self.times = 3

    def __iter__(self):
        return self

    def __next__(self):
        if self.order.type == constants.ORDER_BUY:
            sign = "<="
        elif self.order.type == constants.ORDER_SELL:
            sign = ">="

        while True:
            try:
                """
                    Get first non-blocked order which suit out conditions (price, status, currency) and block it.
                """
                opposite = models.Order.objects.raw('SELECT * '
                                                    'FROM absortium_order '
                                                    'WHERE (status = %s OR status = %s) '
                                                    'AND pg_try_advisory_xact_lock(id) '
                                                    'AND price {sign} %s '
                                                    'AND pair = %s '
                                                    'AND type = %s '
                                                    'AND owner_id <> %s '
                                                    'FOR UPDATE '
                                                    'LIMIT 1 '.format(sign=sign),
                                                    [constants.ORDER_PENDING, constants.ORDER_INIT,
                                                     self.order.price,
                                                     self.order.pair,
                                                     self.order.opposite_type,
                                                     self.order.owner_id])[0]

            except IndexError:
                """
                    Very dirty hack; While orders selection might happen that all orders are locked,
                    so we may end up with skipping the orders processing, in order to low the likelihood of such situation, do it
                    3 times.
                """
                self.times -= 1
                if self.times > 0:
                    continue
                else:
                    raise StopIteration()

            return opposite
