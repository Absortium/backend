from absortium.exceptions import NotEnoughMoneyError
from absortium.mixins.model import OrderMixin
from absortium.wallet.base import get_wallet_client
from django.conf import settings
from django.db import models

from absortium import constants
from core.utils.logging import getLogger
from core.utils.model import calculate_len

__author__ = 'andrew.shvv@gmail.com'
logger = getLogger(__name__)


class Account(models.Model):
    """
        Comment me!
    """
    amount = models.DecimalField(max_digits=constants.ACCOUNT_MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES,
                                 default=0)

    address = models.CharField(max_length=50)

    currency = models.CharField(max_length=calculate_len(constants.AVAILABLE_CURRENCIES))

    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="accounts", null=True)

    class Meta:
        unique_together = ('currency', 'owner', 'address')
        ordering = ('-created',)

    @staticmethod
    def lock(**kwargs):
        return Account.objects.select_for_update().get(**kwargs)

    @staticmethod
    def locks(**kwargs):
        return Account.objects.select_for_update().filter(**kwargs)

    @staticmethod
    def update(pk, **kwargs):
        # update() is converted directly to an SQL statement; it doesn't exec save() on the model
        # instances, and so the pre_save and post_save signals aren't emitted.
        Account.objects.filter(pk=pk).update(**kwargs)


class Order(models.Model, OrderMixin):
    """
    'status' - status of the order:
        'init' - order was created, processed but no opposite order was found for now.
        'pending' - order was created but not fully processed yet.
        'completed' - order was created and fully processed.

    'system' - system in which order is present:
        'own' - order is resides in our system.
        'poloniex' -order is redirected to the poloniex.

    'type' - type of the order:
        sell - order on selling secondary currency.
        buy - order on buying secondary currency.

    'amount' - represent amount of the secondary currency that user want to sell/buy.

    'total' - represent amount of the primary currency that user need to buy/sell in order to get secondary currency.

    'price' - represent the amount of 1 unit of the secondary currency in primary currency.
    primary/secondary are determined as first/second currency in pair string : BTC_ETH => primary=BTC, secondary=ETH

    'created' - order time creation.

    'owner' - user; owner of the order.

    'pair' - represent the two currency between orders are happening.
    Example: BTC_ETH, BTC - primary currency, ETH - secondary currency.
    """

    status = models.CharField(max_length=calculate_len(constants.AVAILABLE_ORDER_STATUSES),
                              default=constants.ORDER_INIT)

    pair = models.CharField(max_length=calculate_len(constants.AVAILABLE_CURRENCY_PAIRS))

    type = models.CharField(max_length=calculate_len(constants.AVAILABLE_ORDER_TYPES))

    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES,
                                 default=0)

    total = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                decimal_places=constants.DECIMAL_PLACES,
                                default=0)

    price = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                decimal_places=constants.DECIMAL_PLACES,
                                default=0)

    created = models.DateTimeField(auto_now_add=True)

    need_approve = models.BooleanField(default=False)
    link = models.ForeignKey('Order', null=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.from_account = None
        self.to_account = None

    @property
    def opposite_type(self):
        if self.type == constants.ORDER_BUY:
            return constants.ORDER_SELL
        elif self.type == constants.ORDER_SELL:
            return constants.ORDER_BUY

    @property
    def primary_currency(self):
        primary_currency = self.pair.split("_")[0]

        if primary_currency not in constants.AVAILABLE_CURRENCIES:
            raise Exception("Not available currency {}".format(primary_currency))

        return primary_currency

    @property
    def secondary_currency(self):
        secondary_currency = self.pair.split("_")[1]

        if secondary_currency not in constants.AVAILABLE_CURRENCIES:
            raise Exception("Not available currency {}".format(secondary_currency))

        return secondary_currency

    @property
    def from_currency(self):
        if self.type == constants.ORDER_BUY:
            return self.primary_currency
        elif self.type == constants.ORDER_SELL:
            return self.secondary_currency

    @property
    def to_currency(self):
        if self.type == constants.ORDER_BUY:
            return self.secondary_currency
        elif self.type == constants.ORDER_SELL:
            return self.primary_currency

    @property
    def from_amount(self):
        if self.type == constants.ORDER_BUY:
            return self.total
        elif self.type == constants.ORDER_SELL:
            return self.amount

    @property
    def to_amount(self):
        if self.type == constants.ORDER_BUY:
            return self.amount
        elif self.type == constants.ORDER_SELL:
            return self.total

    @from_amount.setter
    def from_amount(self, value):
        if self.type == constants.ORDER_BUY:
            self.total = value
        elif self.type == constants.ORDER_SELL:
            self.amount = value

    @to_amount.setter
    def to_amount(self, value):
        if self.type == constants.ORDER_BUY:
            self.amount = value
        elif self.type == constants.ORDER_SELL:
            self.total = value

    @staticmethod
    def lock(**kwargs):
        return Order.objects.select_for_update().get(**kwargs)

    @staticmethod
    def locks(**kwargs):
        return Order.objects.select_for_update().filter(**kwargs)

    @staticmethod
    def update(pk, **kwargs):
        Order.objects.filter(pk=pk).update(**kwargs)


class Deposit(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="deposits")

    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES, default=0)

    currency = models.CharField(max_length=calculate_len(constants.AVAILABLE_CURRENCIES))

    @property
    def address(self):
        return Account.objects.get(owner_id=self.owner_id, currency=self.currency).address

    def process_account(self):
        account = Account.lock(currency=self.currency, owner_id=self.owner_id)

        amount = account.amount + self.amount
        Account.update(pk=account.pk, amount=amount)


class Withdrawal(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="withdrawals")

    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES, default=0)

    currency = models.CharField(max_length=calculate_len(constants.AVAILABLE_CURRENCIES))

    address = models.CharField(max_length=50)

    def process_account(self):
        account = Account.lock(currency=self.currency, owner_id=self.owner_id)

        if account.amount - self.amount >= 0:
            amount = account.amount - self.amount

            client = get_wallet_client(self.currency)
            client.send(self.amount, self.address)

            Account.update(pk=account.pk, amount=amount)
        else:
            raise NotEnoughMoneyError("Not enough money for withdrawal")


class MarketInfo(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    rate = models.DecimalField(max_digits=constants.MAX_DIGITS,
                               decimal_places=constants.DECIMAL_PLACES)

    rate_24h_max = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                       decimal_places=constants.DECIMAL_PLACES)

    rate_24h_min = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                       decimal_places=constants.DECIMAL_PLACES)

    volume_24h = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES, default=0)

    pair = models.CharField(max_length=calculate_len(constants.AVAILABLE_CURRENCY_PAIRS))

    class Meta:
        ordering = ('-created',)
