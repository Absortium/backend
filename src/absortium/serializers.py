from django.contrib.auth.models import User, Group
from rest_framework import serializers

from absortium import constants
from absortium.model.models import Account, Order, Offer, Deposit, Withdrawal, MarketInfo
from absortium.utils import calculate_total_or_amount
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
            kwargs['data'] = calculate_total_or_amount(data)

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
    amount = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                      min_value=constants.DEPOSIT_AMOUNT_MIN_VALUE,
                                      decimal_places=constants.DECIMAL_PLACES)

    class Meta:
        model = Deposit
        fields = ('pk', 'address', 'amount', 'created', 'currency')


class WithdrawSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                      min_value=constants.WITHDRAW_AMOUNT_MIN_VALUE,
                                      decimal_places=constants.DECIMAL_PLACES)

    class Meta:
        model = Withdrawal
        fields = ('pk', 'address', 'amount', 'created', 'currency')


class MarketInfoSerializer(serializers.ModelSerializer):
    pair = MyChoiceField(choices=constants.AVAILABLE_CURRENCY_PAIRS,
                         default=constants.PAIR_BTC_ETH)

    class Meta:
        model = MarketInfo
        fields = ('rate', 'rate_24h_max', 'rate_24h_min', 'volume_24h', 'pair')
