from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from absortium import constants


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

    currency = models.IntegerField()
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)
    price = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                decimal_places=constants.DECIMAL_PLACES)
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name="exchanges")


class Deposit(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name="deposits")
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)


class Withdrawal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name="withdrawals")
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES)

    address = models.CharField(max_length=50)
