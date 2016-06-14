__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from absortium import constants
from absortium.model.models import Account, Exchange, Offer, Deposit, Withdrawal, Test, MarketInfo
from absortium.serializer.fields import MyChoiceField


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `exclude_fields` argument that
    controls which fields should be excluded from serialization.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        exclude_fields = kwargs.pop('exclude_fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if exclude_fields:
            # Drop any fields that are not specified in the `fields` argument.
            disallowed = set(exclude_fields)

            for field_name in disallowed:
                self.fields.pop(field_name)


class OfferSerializer(DynamicFieldsModelSerializer):
    from_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES, write_only=True)
    to_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES, write_only=True)

    amount = serializers.IntegerField(min_value=constants.AMOUNT_MIN_VALUE)
    price = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES,
                                     min_value=constants.PRICE_MIN_VALUE)

    class Meta:
        model = Offer
        fields = ('from_currency', 'to_currency', 'amount', 'price')
        read_only_fields = ('amount', 'price')


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
        WARNING: STATUS FIELD ALWAYS SHOULD BE READ ONLY!
    """
    status = MyChoiceField(choices=constants.AVAILABLE_TASK_STATUS, default=constants.EXCHANGE_INIT, read_only=True)
    amount = serializers.IntegerField(min_value=constants.AMOUNT_MIN_VALUE)
    price = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES,
                                     min_value=constants.PRICE_MIN_VALUE,
                                     max_value=constants.PRICE_MAX_VALUE)

    from_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES)
    to_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES)

    class Meta:
        model = Exchange
        fields = ('pk', 'amount', 'price', 'from_currency', 'to_currency', 'created', 'status')

    def __init__(self, *args, **kwargs):
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
    amount = serializers.IntegerField(min_value=constants.AMOUNT_MIN_VALUE)

    class Meta:
        model = Deposit
        fields = ('pk', 'address', 'amount', 'created')


class WithdrawSerializer(serializers.ModelSerializer):
    address = serializers.CharField()
    amount = serializers.IntegerField(min_value=constants.AMOUNT_MIN_VALUE)

    class Meta:
        model = Withdrawal
        fields = ('pk', 'address', 'amount', 'created')


class MarketInfoSerializer(serializers.ModelSerializer):
    from_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES)
    to_currency = MyChoiceField(choices=constants.AVAILABLE_CURRENCIES)

    class Meta:
        model = MarketInfo
        fields = ('rate', 'rate_24h_max', 'rate_24h_min', 'volume_24h', 'from_currency', 'to_currency')


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ('pk', 'amount')
