__author__ = 'andrew.shvv@gmail.com'

import decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from rest_framework.exceptions import ValidationError

from absortium import constants
from core.utils.logging import getLogger

logger = getLogger(__name__)


class AbsortiumUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Offer(models.Model):
    """
        Offer model represent summarized amount of currency that we want to sell grouped by price.

    primary_currency - represent currency which we will give, for example exchange BTC to XMR,
    primary currency BTC, secondary currency XMR. As input we get string but values stored in Integer, translation from
    string representation "BTC" to integer code 0 happens on the serialization state.

    secondary_currency - represent currency which we will take, for example exchange BTC to XMR,
    primary currency BTC, secondary currency XMR. As input we get string but values stored in Integer, translation from
    string representation "BTC" to integer code 0 happens on the serialization state.

    amount - represent amount of the currency that user want to exchange.

    price - represent the price for the 1 amount of primary currency represented in secondary currency.
    """

    primary_currency = models.IntegerField()
    secondary_currency = models.IntegerField()
    amount = models.DecimalField(max_digits=constants.OFFER_MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)
    price = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                decimal_places=constants.DECIMAL_PLACES)

    class Meta:
        ordering = ('price',)
        unique_together = ('primary_currency', 'secondary_currency', 'price')


class Account(models.Model):
    """
        Comment me!
    """
    amount = models.DecimalField(max_digits=constants.ACCOUNT_MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES, default=0)

    address = models.CharField(max_length=50)
    currency = models.IntegerField()

    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="accounts")

    def update(self, **kwargs):
        # update() is converted directly to an SQL statement; it doesn't call save() on the model
        # instances, and so the pre_save and post_save signals aren't emitted.
        Account.objects.filter(pk=self.pk).update(**kwargs)


class Exchange(models.Model):
    """
        Exchange model represent order for exchange primary currency determined as account currency
        secondary currency determined from the post request.

    currency - represent currency BTC, XMR etc, but values stored in Integer,
    translation from string representation "BTC" to integer code 0 happens on the serialization state.

    amount - represent amount of the currency that  user want to exchange.

    price - represent the price for the 1 amount of base currency he wants to exchange.

    created - order time creation.

    account - account from which exchange is happening.
    """

    status = models.IntegerField()

    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)
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
        self.is_dirty = False

    def process_account(self):

        # Check that we have enough money
        if self.from_account.amount >= self.amount:

            # Subtract money from account because it is locked by exchange
            self.from_account.amount -= self.amount
            self.status = constants.EXCHANGE_PENDING
        else:
            raise ValidationError("Not enough money for exchange creation")

    def update(self, **kwargs):
        Account.objects.filter(pk=self.pk).update(**kwargs)

    def converted_amount(self):
        return self.amount * self.price

    def find_opposite(self):
        converted_price = decimal.Decimal("1.0") / self.price
        return Exchange.objects.filter(
            status=constants.EXCHANGE_PENDING,
            price__lte=converted_price,
            from_currency=self.to_currency).values_list('pk', flat=True)

    def save_fraction(self, converted_amount):
        """
            In case of self.amount > converted_amount create history exchange fraction, in order to track
            for which price and amount our money was exchanged
        """
        if self.amount > converted_amount:
            from copy import deepcopy
            fraction_exchange = deepcopy(self)
            fraction_exchange.amount = converted_amount
            fraction_exchange.pk = None
            fraction_exchange.status = constants.EXCHANGE_COMPLETED
            fraction_exchange.save()

            self.amount -= converted_amount
        else:
            self.status = constants.EXCHANGE_COMPLETED

        return self

    def __sub__(self, exchange):
        if isinstance(exchange, Exchange):
            self.status = constants.EXCHANGE_PENDING

            # convert to currency of this exchange
            converted_amount = exchange.converted_amount()

            self.to_account.amount += exchange.amount  # ETH
            exchange.to_account.amount += converted_amount  # BTC

            exchange.amount = 0
            exchange.status = constants.EXCHANGE_COMPLETED

            self.amount -= converted_amount
            if self.amount == 0:
                self.status = constants.EXCHANGE_COMPLETED
            # save fraction of exchange in order to store history of exchanges
            # self.save_fraction(converted_amount)

            return self
        else:
            return NotImplemented

    def __lt__(self, exchange):
        if isinstance(exchange, Exchange):
            return self.amount < exchange.converted_amount()
        else:
            return NotImplemented

    def __le__(self, exchange):
        if isinstance(exchange, Exchange):
            return self.amount <= exchange.converted_amount()
        else:
            return NotImplemented

    def __gt__(self, exchange):
        if isinstance(exchange, Exchange):
            return self.amount > exchange.converted_amount()
        else:
            return NotImplemented

    def __ge__(self, exchange):
        if isinstance(exchange, Exchange):
            return self.amount >= exchange.converted_amount()
        else:
            return NotImplemented

    def __eq__(self, exchange):
        if isinstance(exchange, Exchange):
            return self.amount == exchange.converted_amount()
        else:
            return NotImplemented

    def __ne__(self, exchange):
        if isinstance(exchange, Exchange):
            return self.amount != exchange.converted_amount()
        else:
            return NotImplemented


class Deposit(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name="deposits")
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)

    def process_account(self):
        amount = self.account.amount + self.amount
        self.account.update(amount=amount)


class Withdrawal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name="withdrawals")
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)

    address = models.CharField(max_length=50)

    def process_account(self):
        if self.account.amount - self.amount >= 0:
            amount = self.account.amount - self.amount
            self.account.update(amount=amount)
        else:
            raise ValidationError("Not enough money for withdrawal")


class Test(models.Model):
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="tests")
