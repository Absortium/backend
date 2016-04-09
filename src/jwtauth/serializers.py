__author__ = 'andrew.shvv@gmail.com'

from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER

from core.utils.logging import getLogger

logger = getLogger(__name__)


class SocialJWTSerializer(serializers.Serializer):
    """
        Serializer class used to validate by social providers.
        Returns a JSON Web Token that can be used to authenticate later calls.
    """

    code = serializers.CharField(max_length=100)
    provider = serializers.CharField(max_length=100)
    redirect_uri = serializers.CharField(max_length=100)
    client_id = serializers.CharField(max_length=100)

    @property
    def object(self):
        return self.validated_data


class OAuth2Serializer(serializers.Serializer):
    code = serializers.CharField(max_length=100)
    redirect_uri = serializers.CharField(max_length=100)
    client_id = serializers.CharField(max_length=100)

    @property
    def object(self):
        return self.validated_data


class OAuth1Serializer(serializers.Serializer):
    oauth_token = serializers.CharField(max_length=100, required=False)
    oauth_verifier = serializers.CharField(max_length=100, required=False)

    @property
    def object(self):
        return self.validated_data


class BasicJWTSerializer(JSONWebTokenSerializer):
    """
        Serializer class used only us wrapper under JSONWebTokenSerializer in order to have more obvious name
        Returns a JSON Web Token that can be used to authenticate later calls.
    """
    pass
