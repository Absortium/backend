__author__ = 'andrew.shvv@gmail.com'

import six
from django.contrib.auth.models import User, Group
from rest_framework import serializers

from absortium import constants
from absortium.models import Order, Offer, Address


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class MyChoiceField(serializers.Field):
    """
        This class used for translation incoming strings values to
        integer representation by the given mapping dict.
    """

    def __init__(self, choices):
        super().__init__()
        self.to_internal = choices
        self.to_repr = {value: key for key, value in choices.items()}

    def to_internal_value(self, data):
        if not isinstance(data, six.text_type):
            msg = 'Incorrect type. Expected a string, but got %s'
            raise serializers.ValidationError(msg % type(data).__name__)

        data = data.lower()
        return self.to_internal[data]

    def to_representation(self, value):
        if not isinstance(value, six.integer_types):
            msg = 'Incorrect type. Expected a int, but got %s'
            raise serializers.ValidationError(msg % type(value).__name__)

        return self.to_repr[value]


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


class OrderSerializer(serializers.ModelSerializer):
    type = MyChoiceField(choices=constants.AVAILABLE_ORDER_TYPES)
    pair = MyChoiceField(choices=constants.AVAILABLE_PAIRS)

    amount = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                      decimal_places=constants.DECIMAL_PLACES,
                                      min_value=constants.AMOUNT_MIN_VALUE)
    price = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES,
                                     min_value=constants.PRICE_MIN_VALUE)

    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Order
        fields = ('pk', 'type', 'pair', 'amount', 'price', 'owner')


class OfferSerializer(DynamicFieldsModelSerializer):
    type = MyChoiceField(choices=constants.AVAILABLE_ORDER_TYPES)
    pair = MyChoiceField(choices=constants.AVAILABLE_PAIRS)

    amount = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                      decimal_places=constants.DECIMAL_PLACES,
                                      min_value=constants.AMOUNT_MIN_VALUE)
    price = serializers.DecimalField(max_digits=constants.MAX_DIGITS,
                                     decimal_places=constants.DECIMAL_PLACES,
                                     min_value=constants.PRICE_MIN_VALUE)

    class Meta:
        model = Offer
        fields = ('pair', 'type', 'amount', 'price')


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('address', 'currency')
