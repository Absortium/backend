from rest_framework import serializers

__author__ = 'andrew.shvv@gmail.com'


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
