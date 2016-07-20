from absortium import constants
from absortium.exceptions import NotEnoughMoneyError
from absortium.model import models
from absortium.model.locks import get_opposites, lockaccounts
from core.utils.logging import getLogger

__author__ = 'andrew.shvv@gmail.com'
logger = getLogger(__name__)


def operation_wrapper(func):
    def decorator(self, obj):
        if isinstance(obj, models.Order):
            value = obj.amount
        elif isinstance(obj, (int, float)):
            value = obj
        else:
            return NotImplemented

        return func(self, value)

    return decorator


class OrderMixin():
    def process(self):
        order = self

        history = []

        for opposite in get_opposites(order):
            with lockaccounts(opposite):
                if order >= opposite:
                    (fraction, order) = order - opposite

                    if order is None:
                        order = fraction
                        break
                    else:
                        history.append(fraction)

                elif order < opposite:
                    """
                        In this case order will be in the ORDER_COMPLETED status, so just break loop and
                        than add order to the history
                    """
                    (_, opposite) = opposite - order
                    break

        return history + [order]

    def freeze_money(self):
        # Check that we have enough money
        if self.from_account.amount >= self.from_amount:

            # Subtract money from account because it is locked by order
            self.from_account.amount -= self.from_amount
        else:
            raise NotEnoughMoneyError("Not enough money for order creation/update")

    def unfreeze_money(self):
        self.from_account.amount += self.from_amount

    def split(self, opposite):
        """
            Divide order on two parts.
        """
        order = self

        if order.from_amount <= opposite.to_amount:
            fraction = order
            return fraction, None
        else:
            from copy import deepcopy
            fraction = deepcopy(order)
            fraction.from_amount = opposite.to_amount
            fraction.to_amount = opposite.from_amount
            fraction.to_account = order.to_account
            fraction.from_account = order.from_account
            fraction.pk = None

            order.from_amount -= opposite.to_amount
            order.to_amount -= opposite.from_amount

            return fraction, order

    def merge(self, opposite):
        fraction = self

        fraction.to_account.amount += opposite.from_amount
        opposite.to_account.amount += opposite.to_amount

        fraction.status = constants.ORDER_COMPLETED
        opposite.status = constants.ORDER_COMPLETED

    def __sub__(self, obj):
        if isinstance(obj, models.Order):
            opposite = obj
            order = self
            order.status = constants.ORDER_PENDING

            # save fraction of order to store history of orders
            (fraction, order) = order.split(opposite)

            fraction.link = opposite
            opposite.link = fraction

            if fraction.need_approve or opposite.need_approve:
                # wait for approving
                fraction.status = constants.ORDER_APPROVING
                opposite.status = constants.ORDER_APPROVING

            else:
                # merge opposite orders
                fraction.merge(opposite)

            if order is not None:
                fraction.save()

            return fraction, order
        else:
            return NotImplemented

    @operation_wrapper
    def __lt__(self, value):
        return self.amount < value

    @operation_wrapper
    def __gt__(self, value):
        return self.amount > value

    @operation_wrapper
    def __le__(self, value):
        return self.amount <= value

    @operation_wrapper
    def __ge__(self, value):
        return self.amount >= value

    @operation_wrapper
    def __eq__(self, value):
        return self.amount == value

    @operation_wrapper
    def __ne__(self, value):
        return self.amount != value
