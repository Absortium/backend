__author__ = 'andrew.shvv@gmail.com'

import decimal

from django.conf import settings
from django.db import models
from rest_framework.exceptions import ValidationError

from absortium import constants
from absortium.wallet.base import get_wallet_client
from core.utils.logging import getLogger

logger = getLogger(__name__)


class Offer(models.Model):
    """
        Offer model represent summarized amount of currency that we want to sell grouped by price.

    from_currency/to_currency; example exchange BTC to XMR, from_currency will be BTC, to_currency will be XMR.
    As input we get string but values stored in Integer, translation from
    string representation "BTC" to integer code 0 happens on the serialization state.

    amount - represent amount of the currency that user want to exchange.

    price - represent the price for the 1 amount of primary currency represented in secondary currency.
    """

    from_currency = models.IntegerField()
    to_currency = models.IntegerField()
    amount = models.BigIntegerField(default=0)
    price = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                decimal_places=constants.DECIMAL_PLACES)

    class Meta:
        ordering = ('price',)
        unique_together = ('to_currency', 'from_currency', 'price')


class Account(models.Model):
    """
        Comment me!
    """
    amount = models.BigIntegerField(default=0)

    address = models.CharField(max_length=50)
    currency = models.IntegerField()

    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="accounts")

    class Meta:
        unique_together = ('currency', 'owner', 'address')
        ordering = ('-created',)

    def update(self, **kwargs):
        # update() is converted directly to an SQL statement; it doesn't exec save() on the model
        # instances, and so the pre_save and post_save signals aren't emitted.
        Account.objects.filter(pk=self.pk).update(**kwargs)


def operation_wrapper(func):
    def decorator(self, obj):
        if isinstance(obj, Exchange):
            value = obj.converted_amount()
        elif isinstance(obj, (int, float)):
            value = obj
        else:
            return NotImplemented

        return func(self, value)

    return decorator


class Exchange(models.Model):
    """
        Exchange model represent order for exchange primary currency determined as account currency
        secondary currency determined from the post request.

    from_currency/to_currency; example exchange BTC to XMR, from_currency will be BTC, to_currency will be XMR.
    As input we get string but values stored in Integer, translation from
    string representation "BTC" to integer code 0 happens on the serialization state.

    amount - represent amount of the currency that  user want to exchange.

    price - represent the price for the 1 amount of base currency he wants to exchange.

    created - exchange time creation.

    owner - user; owner of the exchange

    status - status of the exhcange:
        init -
        pending -
        completed -

    """

    status = models.IntegerField()

    amount = models.BigIntegerField()
    price = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                decimal_places=constants.DECIMAL_PLACES)

    created = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="exchanges")

    from_currency = models.IntegerField()
    to_currency = models.IntegerField()

    class Meta:
        ordering = ['-price', 'created']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.from_account = None
        self.to_account = None

    def process_account(self):
        # Check that we have enough money
        if self.from_account.amount >= self.amount:

            # Subtract money from account because it is locked by exchange
            self.from_account.amount -= self.amount
            self.save()
        else:
            raise ValidationError("Not enough money for exchange creation")

    def update(self, **kwargs):
        Account.objects.filter(pk=self.pk).update(**kwargs)

    def converted_amount(self):
        return self.amount * self.price

    def split(self, converted_amount):
        """
            Divide exchange on two parts - completed part and remain part
        """

        if self.amount == converted_amount:
            self.status = constants.EXCHANGE_COMPLETED
            completed = self
        else:
            from copy import deepcopy
            completed = deepcopy(self)
            completed.amount = converted_amount
            completed.pk = None
            completed.status = constants.EXCHANGE_COMPLETED
            completed.save()

            self.amount -= converted_amount

        return completed, self

    def __sub__(self, obj):
        if isinstance(obj, Exchange):
            opposite = obj
            exchange = self

            exchange.status = constants.EXCHANGE_PENDING
            opposite.status = constants.EXCHANGE_COMPLETED

            # convert to currency of this exchange
            converted_amount = opposite.converted_amount()
            amount = opposite.amount

            exchange.to_account.amount += amount  # ETH
            opposite.to_account.amount += converted_amount  # BTC

            # save fraction of exchange in order to store history of exchanges
            (completed, exchange) = exchange.split(converted_amount)

            return completed, exchange
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


class Deposit(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name="deposits")
    amount = models.BigIntegerField()

    def process_account(self):
        amount = self.account.amount + self.amount
        self.account.update(amount=amount)


class Withdrawal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name="withdrawals")
    amount = models.BigIntegerField()

    address = models.CharField(max_length=50)

    def process_account(self):
        if self.account.amount - self.amount >= 0:
            amount = self.account.amount - self.amount
            self.account.update(amount=amount)
        else:
            raise ValidationError("Not enough money for withdrawal")


class MarketInfo(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    rate = models.DecimalField(max_digits=constants.MAX_DIGITS,
                               decimal_places=constants.DECIMAL_PLACES)
    rate_24h_max = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                       decimal_places=constants.DECIMAL_PLACES)
    rate_24h_min = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                       decimal_places=constants.DECIMAL_PLACES)
    volume_24h = models.BigIntegerField()

    from_currency = models.IntegerField()
    to_currency = models.IntegerField()

    class Meta:
        ordering = ('-created',)


class Test(models.Model):
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="tests")
