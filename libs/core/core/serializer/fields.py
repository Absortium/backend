import six
from rest_framework import serializers

__author__ = 'andrew.shvv@gmail.com'


class MyDecimalField(serializers.DecimalField):
    def validate_precision(self, value):
        try:
            return super().validate_precision(value)
        except serializers.ValidationError:
            return round(value, self.decimal_places)


class MySerializerMethodField(serializers.SerializerMethodField):
    def __init__(self, read_only=True, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        kwargs['read_only'] = read_only
        super(serializers.SerializerMethodField, self).__init__(**kwargs)


class MyChoiceField(serializers.Field):
    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = choices

    def to_internal_value(self, value):
        if not isinstance(value, six.text_type):
            msg = 'Incorrect type. Expected a string, but got %s'
            raise serializers.ValidationError(msg % type(value).__name__)

        value = value.lower()
        if value not in self.choices:
            raise serializers.ValidationError("Field not in the ['{}']".format(self.choices))

        return value

    def to_representation(self, value):
        if not isinstance(value, six.text_type):
            msg = 'Incorrect type. Expected a string, but got %s'
            raise serializers.ValidationError(msg % type(value).__name__)

        return value
