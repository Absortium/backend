import hashlib
import hmac

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import PermissionDenied

from .models import Client

__author__ = 'andrew.shvv@gmail.com'


class APIKeyAuth(BaseAuthentication):
    def authenticate(self, request):
        if 'HTTP_ACCESS_KEY' not in request.META:
            return None

        if 'HTTP_ACCESS_SIGN' not in request.META:
            return None

        if 'HTTP_ACCESS_TIMESTAMP' not in request.META:
            return None

        if 'HTTP_VERSION' not in request.META:
            return None

        key = request.META['HTTP_ACCESS_KEY']
        signature = request.META['HTTP_ACCESS_SIGN']

        # TODO: raise PermissionDenied if timestamp is expired!
        timestamp = request.META['HTTP_ACCESS_TIMESTAMP']
        version = request.META['HTTP_ACCESS_VERSION']
        data = request.body

        try:
            client = Client.objects.get(api_key=key)
        except Client.DoesNotExist:
            return None, None

        if signature == hmac.new(client.api_secret.encode(), data, hashlib.sha256).hexdigest():
            return client.owner, None
        else:
            raise PermissionDenied("Non-valid signature was specified")
