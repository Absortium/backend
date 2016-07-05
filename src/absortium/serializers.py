import decimal
from decimal import Decimal

from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from absortium import constants
from absortium.model.models import Account, Exchange, Offer, Deposit, Withdrawal, MarketInfo
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
                           read_only=True)

    from_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES, write_only=True)
    to_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES, write_only=True)

    amount = serializers.DecimalField(max_digits=constants.OFFER_MAX_DIGITS,
                                      decimal_places=constants.DECIMAL_PLACES,
                                      read_only=True)

    price = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES,
                                     min_value=constants.PRICE_MIN_VALUE,
                                     read_only=True)

    class Meta:
        model = Offer
        fields = ('from_currency', 'to_currency', 'amount', 'price', 'system')


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


class ExchangeSerializer(serializers.ModelSerializer):
    """
        WARNING: 'status' AND 'type' FIELDS SHOULD ALWAYS BE READ ONLY!
    """
    status = MyChoiceField(choices=constants.AVAILABLE_TASK_STATUS, default=constants.EXCHANGE_INIT, read_only=True)
    system = MyChoiceField(choices=constants.AVAILABLE_SYSTEMS, default=constants.SYSTEM_OWN, read_only=True)

    from_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES)
    to_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES)

    from_amount = serializers.DecimalField(max_digits=constants.OFFER_MAX_DIGITS,
                                           decimal_places=constants.DECIMAL_PLACES)
    to_amount = serializers.DecimalField(max_digits=constants.OFFER_MAX_DIGITS,
                                         decimal_places=constants.DECIMAL_PLACES)

    price = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES,
                                     min_value=constants.PRICE_MIN_VALUE)

    class Meta:
        model = Exchange
        fields = ('pk', 'price', 'created', 'status', 'system',
                  'to_amount', 'from_amount',
                  'from_currency', 'to_currency')

    def __init__(self, *args, **kwargs):
        data = kwargs.get('data')

        if data is not None:
            from_amount = data.get('from_amount')
            to_amount = data.get('to_amount')

            if to_amount is not None and from_amount is not None:
                raise ValidationError("only one of the 'to_amount' or 'from_amount' fields should be presented")

            elif to_amount is None and from_amount is None:
                raise ValidationError("one of the 'to_amount' or 'from_amount' fields should be presented")

            price = data.get('price')
            if price is None:
                raise ValidationError("'price' field should be present")

            try:
                price = round(Decimal(price), constants.DECIMAL_PLACES)
            except decimal.InvalidOperation:
                raise ValidationError("'price' field should be decimal serializable")

            if from_amount is not None and to_amount is None:
                try:
                    from_amount = round(Decimal(from_amount), constants.DECIMAL_PLACES)
                except decimal.InvalidOperation:
                    raise ValidationError("'from_amount' field should be decimal serializable")

                data['to_amount'] = str(round(from_amount * price, constants.DECIMAL_PLACES))

            elif to_amount is not None and from_amount is None:
                try:
                    to_amount = round(Decimal(to_amount), constants.DECIMAL_PLACES)
                except decimal.InvalidOperation:
                    raise ValidationError("'to_amount' field should be decimal serializable")

                data['from_amount'] = str(round(to_amount / price, constants.DECIMAL_PLACES))

            kwargs['data'] = data

        super().__init__(*args, **kwargs)
        self._object = None

    def object(self, **kwargs):
        if not self._object:
            validated_data = dict(
                list(self.validated_data.items()) +
                list(kwargs.items())
            )

            self._object = Exchange(**validated_data)
        return self._object

    def validate(self, attrs):
        if attrs['from_currency'] == attrs['to_currency']:
            raise ValidationError("Exchange on the same currency not make sense")

        return super().validate(attrs)


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
    from_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES)
    to_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES)

    class Meta:
        model = MarketInfo
        fields = ('rate', 'rate_24h_max', 'rate_24h_min', 'volume_24h', 'from_currency', 'to_currency')
