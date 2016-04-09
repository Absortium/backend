__author__ = 'andrew.shvv@gmail.com'

from urllib.parse import parse_qsl

import requests
from django.conf import settings
from django.contrib.auth import authenticate
from requests_oauthlib import OAuth1
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import ObtainJSONWebToken, VerifyJSONWebToken, RefreshJSONWebToken

from core.utils.logging import getLogger
from jwtauth.exceptions import Http400
from jwtauth.serializers import BasicJWTSerializer, OAuth2Serializer, OAuth1Serializer

jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER

logger = getLogger(__name__)


class ViewObtainSocialOAuth2(APIView):
    """
        View class used for social authentication with OAuth2 protocol.
    """

    permission_classes = ()
    authentication_classes = ()
    serializer_class = OAuth2Serializer

    def get_serializer(self, data, *args, **kwargs):
        return OAuth2Serializer(data=data, *args, **kwargs)

    def post(self, request, provider, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            params = serializer.object
            params['auth_type'] = 'oauth2'
            params['provider'] = provider

            user = authenticate(**params)
            if user:
                if not user.is_active:
                    raise Http400("User account is disabled.")

                payload = jwt_payload_handler(user)
                token = jwt_encode_handler(payload)
                response_data = jwt_response_payload_handler(token, user, request)

                return Response(response_data)
            else:
                msg = "Looks like there is no such provider: {}".format(provider)
                raise Http400(msg)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ViewObtainSocialOAuth1(APIView):
    """
        View class used for social authentication with OAuth1 protocol.
    """
    permission_classes = ()
    authentication_classes = ()
    serializer_class = OAuth1Serializer

    def get_oauth_token(self):
        request_token_url = 'https://api.twitter.com/oauth/request_token'

        credentials = {
            'client_key': getattr(settings, 'SOCIAL_AUTH_TWITTER_OAUTH1_KEY'),
            'client_secret': getattr(settings, 'SOCIAL_AUTH_TWITTER_OAUTH1_SECRET'),
            'callback_uri': getattr(settings, 'SOCIAL_AUTH_TWITTER_OAUTH1_CALLBACK_URL'),
        }
        oauth = OAuth1(**credentials)
        r = requests.post(request_token_url, auth=oauth)
        oauth_token = dict(parse_qsl(r.text))
        return oauth_token

    def post(self, request, provider, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            params = serializer.object

            # If we haven't 'oauth_token' and 'oauth_verifier' that means that we should
            # get token and then redirect to this server again
            if not (params.get('oauth_token') and params.get('oauth_verifier')):
                oauth_token = self.get_oauth_token()
                return Response(oauth_token)

            # Every social django backend checks 'auth_type' and 'provider', in order
            # to not proceed execution in case of not suitable parameters.
            # Example: Google shouldn't try to fetch twitter user.
            params['auth_type'] = 'oauth1'
            params['provider'] = provider

            user = authenticate(**params)

            if user:
                if not user.is_active:
                    raise Http400("User account is disabled.")

                payload = jwt_payload_handler(user)
                token = jwt_encode_handler(payload)
                response_data = jwt_response_payload_handler(token, user, request)

                return Response(response_data)
            else:
                msg = "Looks like there is no such provider: {}".format(provider)
                raise Http400(msg)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ViewVerify(VerifyJSONWebToken):
    """
        View class used only us wrapper under VerifyJSONWebToken in order to have more obvious name
        Verify JSON Web Token signature, compare in with payload.
    """
    pass


class ViewRefresh(RefreshJSONWebToken):
    """
        View class used only us wrapper under RefreshJSONWebToken in order to have more obvious name
        Returns a newly generated JSON Web Token that can be used to authenticate later calls.
    """
    pass


class ViewObtainBasic(ObtainJSONWebToken):
    """
        View class used only us wrapper under ObtainJSONWebToken in order to have more obvious name
        Obtain JSON Web Token by email/password.
    """
    serializer_class = BasicJWTSerializer
