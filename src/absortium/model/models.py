from django.conf import settings
from django.db import models
from rest_framework.exceptions import ValidationError

from absortium import constants
from absortium.wallet.base import get_wallet_client
from core.utils.logging import getLogger

__author__ = 'andrew.shvv@gmail.com'
logger = getLogger(__name__)


def calculate_len(choices):
    """
        Calculate length for choice filed in django model.
    """
    return max([len(t) for t in choices]) + 1


class Offer(models.Model):
    """
        Offer model represent summarized amount of currency that we want to sell grouped by price.

    from_currency/to_currency; example order BTC to XMR, from_currency will be BTC, to_currency will be XMR.
    As input we get string but values stored in Integer, translation from
    string representation "BTC" to integer code 0 happens on the serialization state.

    amount - represent amount of the currency that user want to order.

    price - represent the price for the 1 amount of primary currency represented in secondary currency.
    """
    system = models.CharField(max_length=calculate_len(constants.AVAILABLE_SYSTEMS),
                              default=constants.SYSTEM_OWN)

    pair = models.CharField(max_length=calculate_len(constants.AVAILABLE_CURRENCY_PAIRS))

    type = models.CharField(max_length=calculate_len(constants.AVAILABLE_ORDER_TYPES))

    amount = models.DecimalField(max_digits=constants.OFFER_MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES,
                                 default=0)

    price = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                decimal_places=constants.DECIMAL_PLACES)

    class Meta:
        ordering = ('price',)
        unique_together = ('pair', 'price', 'system', 'type')

    def update(self, **kwargs):
        # update() is converted directly to an SQL statement; it doesn't exec save() on the model
        # instances, and so the pre_save and post_save signals aren't emitted.
        Offer.objects.filter(pk=self.pk).update(**kwargs)

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

    def update(self, **kwargs):
        # update() is converted directly to an SQL statement; it doesn't exec save() on the model
        # instances, and so the pre_save and post_save signals aren't emitted.
        Account.objects.filter(pk=self.pk).update(**kwargs)


def operation_wrapper(func):
    def decorator(self, obj):
        if isinstance(obj, Order):
            value = obj.amount
        elif isinstance(obj, (int, float)):
            value = obj
        else:
            return NotImplemented

        return func(self, value)

    return decorator


class Order(models.Model):
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

    system = models.CharField(max_length=calculate_len(constants.AVAILABLE_SYSTEMS),
                              default=constants.SYSTEM_OWN)

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

    class Meta:
        ordering = ['-price', 'created']

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

    def freeze_money(self):
        # Check that we have enough money
        if self.from_account.amount >= self.from_amount:

            # Subtract money from account because it is locked by order
            self.from_account.amount -= self.from_amount
            self.save()
        else:
            raise ValidationError("Not enough money for order creation")

    def unfreeze_money(self):
        self.from_account.amount += self.from_amount
        self.save()

    def update(self, **kwargs):
        Account.objects.filter(pk=self.pk).update(**kwargs)

    def split(self, opposite):
        """
            Divide order on two parts.
        """
        order = self

        if order.from_amount <= opposite.to_amount:
            fraction = order
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
        if isinstance(obj, Order):
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

            if fraction.pk is None:
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


class Deposit(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name="deposits")
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES, default=0)

    def process_account(self):
        amount = self.account.amount + self.amount
        self.account.update(amount=amount)


class Withdrawal(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name="withdrawals")
    amount = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                 decimal_places=constants.DECIMAL_PLACES, default=0)

    address = models.CharField(max_length=50)

    def process_account(self):
        if self.account.amount - self.amount >= 0:
            amount = self.account.amount - self.amount
            self.account.update(amount=amount)

            client = get_wallet_client(self.account.currency)
            client.send(self.amount, self.address)
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

    volume_24h = models.DecimalField(max_digits=constants.MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES, default=0)

    pair = models.CharField(max_length=calculate_len(constants.AVAILABLE_CURRENCY_PAIRS))

    class Meta:
        ordering = ('-created',)
