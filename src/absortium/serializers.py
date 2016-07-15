import decimal
from decimal import Decimal

from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from absortium import constants
from absortium.model.models import Account, Order, Offer, Deposit, Withdrawal, MarketInfo
from core.serializer.fields import MyChoiceField
from core.serializer.serializers import DynamicFieldsModelSerializer
from core.utils.logging import getPrettyLogger

__author__ = 'andrew.shvv@gmail.com'

logger = getPrettyLogger(__name__)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class OfferSerializer(DynamicFieldsModelSerializer):
    system = MyChoiceField(choices=constants.AVAILABLE_SYSTEMS,
                           default=constants.SYSTEM_OWN,
                           write_only=True)

    type = MyChoiceField(choices=constants.AVAILABLE_ORDER_TYPES)

    pair = MyChoiceField(choices=constants.AVAILABLE_CURRENCY_PAIRS,
                         default=constants.PAIR_BTC_ETH)

    amount = serializers.DecimalField(max_digits=constants.OFFER_MAX_DIGITS,
                                      decimal_places=constants.DECIMAL_PLACES,
                                      read_only=True)

    price = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES,
                                     min_value=constants.PRICE_MIN_VALUE,
                                     read_only=True)

    class Meta:
        model = Offer
        fields = ('pair', 'type', 'amount', 'price', 'system')


class AccountSerializer(serializers.ModelSerializer):
    currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES)

    class Meta:
        model = Account
        fields = ('pk', 'address', 'currency', 'amount')
        read_only_fields = ('address', 'amount')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._object = None

    def object(self, **kwargs):
        if not self._object:
            validated_data = dict(
                list(self.validated_data.items()) +
                list(kwargs.items())
            )

            self._object = Account(**validated_data)
        return self._object


class OrderSerializer(serializers.ModelSerializer):
    """
        WARNING: 'status' AND 'type' FIELDS SHOULD ALWAYS BE READ ONLY!
    """
    status = MyChoiceField(choices=constants.AVAILABLE_ORDER_STATUSES, default=constants.ORDER_INIT, read_only=True)

    system = MyChoiceField(choices=constants.AVAILABLE_SYSTEMS, default=constants.SYSTEM_OWN, read_only=True)

    type = MyChoiceField(choices=constants.AVAILABLE_ORDER_TYPES)

    pair = MyChoiceField(choices=constants.AVAILABLE_CURRENCY_PAIRS,
                         default=constants.PAIR_BTC_ETH)

    amount = serializers.DecimalField(max_digits=constants.OFFER_MAX_DIGITS,
                                      decimal_places=constants.DECIMAL_PLACES)
    total = serializers.DecimalField(max_digits=constants.OFFER_MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES)

    price = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES,
                                     min_value=constants.PRICE_MIN_VALUE)

    need_approve = serializers.BooleanField(default=False)

    class Meta:
        model = Order
        fields = ('pk', 'price', 'created', 'status', 'type', 'system', 'amount', 'total', 'pair', 'need_approve')

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data')

        if data is not None:
            amount = data.get('amount')
            total = data.get('total')

            if total is not None and amount is not None:
                raise ValidationError("only one of the 'amount' or 'total' fields should be presented")

            elif total is None and amount is None:
                raise ValidationError("one of the 'amount' or 'total' fields should be presented")

            price = data.get('price')
            if price is None:
                raise ValidationError("'price' field should be present")

            try:
                price = round(Decimal(price), constants.DECIMAL_PLACES)
            except decimal.InvalidOperation:
                raise ValidationError("'price' field should be decimal serializable")

            if amount is not None and total is None:
                try:
                    amount = round(Decimal(amount), constants.DECIMAL_PLACES)
                except decimal.InvalidOperation:
                    raise ValidationError("'amount' field should be decimal serializable")

                data['total'] = str(round(amount * price, constants.DECIMAL_PLACES))

            elif total is not None and amount is None:
                try:
                    total = round(Decimal(total), constants.DECIMAL_PLACES)
                except decimal.InvalidOperation:
                    raise ValidationError("'total' field should be decimal serializable")

                data['amount'] = str(round(total / price, constants.DECIMAL_PLACES))

            kwargs['data'] = data

        super().__init__(*args, **kwargs)
        self._object = None

    def object(self, **kwargs):
        if not self._object:
            validated_data = dict(
                list(self.validated_data.items()) +
                list(kwargs.items())
            )

            self._object = Order(**validated_data)
        return self._object


class DepositSerializer(serializers.ModelSerializer):
    address = serializers.ReadOnlyField(source='account.address')
    amount = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                      min_value=constants.DEPOSIT_AMOUNT_MIN_VALUE,
                                      decimal_places=constants.DECIMAL_PLACES)

    class Meta:
        model = Deposit
        fields = ('pk', 'address', 'amount', 'created')


class WithdrawSerializer(serializers.ModelSerializer):
    address = serializers.CharField()
    amount = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                      min_value=constants.WITHDRAW_AMOUNT_MIN_VALUE,
                                      decimal_places=constants.DECIMAL_PLACES)

    class Meta:
        model = Withdrawal
        fields = ('pk', 'address', 'amount', 'created')


class MarketInfoSerializer(serializers.ModelSerializer):
    pair = MyChoiceField(choices=constants.AVAILABLE_CURRENCY_PAIRS,
                         default=constants.PAIR_BTC_ETH)

    class Meta:
        model = MarketInfo
        fields = ('rate', 'rate_24h_max', 'rate_24h_min', 'volume_24h', 'pair')
