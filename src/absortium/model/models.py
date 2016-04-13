from django.conf import settings

from django.db import models

from absortium import constants

from django.contrib.auth.models import User


class AbsortiumUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Order(models.Model):
    """
        Order model represent orders for exchange currency

    type - represent type of the order sell/buy , but values stored in Integer,
    translation from string representation "sell" to integer code 0 happens on the serialization state.

    pair - represent currency pairs BTC_ETH, BTC_XMR etc, but values stored in Integer,
    translation from string representation "sell" to integer code 0 happens on the serialization state.

    amount - represent amount of the currency that  user want to exchange.

    price - represent the price for the 1 amount of currency he wants to exchange.

    created - order time creation.

    owner - owner of the order.
    """

    type = models.IntegerField()
    pair = models.IntegerField()
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)
    price = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                decimal_places=constants.DECIMAL_PLACES)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)

    class Meta:
        ordering = ('price',)


class Offer(models.Model):
    """
        Offer model represent summarized amount of currency by the given price.
        Example:
            Order(price=1.0. amount=1.0, type="sell", pair="BTC_ETH")
            Order(price=1.0. amount=1.0, type="sell", pair="BTC_ETH")
            Order(price=1.0. amount=1.0, type="sell", pair="BTC_ETH")

            is one offer Offer(price=1.0. amount=3.0, type="sell", pair="BTC_ETH")


    type - represent type of the order sell/buy , but values stored in Integer,
    translation from string representation "sell" to integer code 0 happens on the serialization state.

    pair - represent currency pairs BTC_ETH, BTC_XMR etc, but values stored in Integer,
    translation from string representation "sell" to integer code 0 happens on the serialization state.

    amount - represent amount of the currency that  user want to exchange.

    price - represent the price for the 1 amount of currency he wants to exchange.
    """

    type = models.IntegerField()
    pair = models.IntegerField()
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)
    price = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                decimal_places=constants.DECIMAL_PLACES)

    class Meta:
        ordering = ('price',)


class Address(models.Model):
    """
    """

    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES, default=0)

    address = models.TextField()
    currency = models.IntegerField()

    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)

    class Meta:
        unique_together = ("currency", "address")


class Account(models.Model):
    """
        Comment me!
    """
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES, default=0)

    address = models.TextField()
    currency = models.IntegerField()

    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="accounts")


class Exchange(models.Model):
    """
        Exchange model represent order for exchange base determined as account currency
        secondary currency determined from post request.

    currency - represent currency BTC, XMR etc, but values stored in Integer,
    translation from string representation "BTC" to integer code 0 happens on the serialization state.

    amount - represent amount of the currency that  user want to exchange.

    price - represent the price for the 1 amount of base currency he wants to exchange.

    created - order time creation.

    account - account from which exchange is happening.
    """

    currency = models.IntegerField()
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)
    price = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                decimal_places=constants.DECIMAL_PLACES)
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name="exchanges")