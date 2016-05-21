# coding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

import requests

from .auth import HMACAuth
from .compat import imap, urljoin, quote
from .util import check_uri_security, encode_params

ETHCLIENT_CRT_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'ca-ethwallet.crt')

ETHCLIENT_CALLBACK_PUBLIC_KEY_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'ethwallet-callback.pub')


class Client(object):
    """ API Client for the ethwallet API.

    Entry point for making requests to the ethwallet API. Provides helper methods
    for common API endpoints, as well as niceties around response verification
    and formatting.

    Any errors will be raised as exceptions. These exceptions will always be
    subclasses of `ethwallet.error.APIError`. HTTP-related errors will also be
    subclasses of `requests.HTTPError`.
    """
    VERIFY_SSL = True
    API_VERSION = '2016-05-17'

    cached_callback_public_key = None

    def __init__(self, api_key, api_secret, base_api_uri, api_version=None):
        if not api_key:
            raise ValueError('Missing `api_key`.')
        if not api_secret:
            raise ValueError('Missing `api_secret`.')

        # Allow passing in a different API base.
        self.BASE_API_URI = check_uri_security(base_api_uri)

        self.API_VERSION = api_version or self.API_VERSION

        # Set up a requests session for interacting with the API.
        self.session = self._build_session(HMACAuth, api_key, api_secret, self.API_VERSION)

    def _build_session(self, auth_class, *args, **kwargs):
        """Internal helper for creating a requests `session` with the correct
        authentication handling."""
        session = requests.session()
        session.auth = auth_class(*args, **kwargs)
        session.headers.update({'Accept': 'application/json',
                                'Content-Type': 'application/json',
                                'User-Agent': 'ethwallet/python/3.0'})
        return session

    def _create_api_uri(self, *parts):
        """Internal helper for creating fully qualified endpoint URIs."""
        return urljoin(self.BASE_API_URI, '/'.join(imap(quote, parts)))

    def _request(self, method, *relative_path_parts, **kwargs):
        """Internal helper for creating HTTP requests to the ethwallet API.

        Raises an APIError if the response is not 20X. Otherwise, returns the
        response object. Not intended for direct use by API consumers.
        """
        uri = self._create_api_uri(*relative_path_parts)
        data = kwargs.get('data', None)
        if data and isinstance(data, dict):
            kwargs['data'] = encode_params(data)
        if self.VERIFY_SSL:
            kwargs.setdefault('verify', ETHCLIENT_CRT_PATH)
        else:
            kwargs.setdefault('verify', False)
        kwargs.update(verify=self.VERIFY_SSL)
        response = getattr(self.session, method)(uri, **kwargs)
        return response

    def _get(self, *args, **kwargs):
        return self._request('get', *args, **kwargs)

    def _post(self, *args, **kwargs):
        return self._request('post', *args, **kwargs)

    def _put(self, *args, **kwargs):
        return self._request('put', *args, **kwargs)

    def _delete(self, *args, **kwargs):
        return self._request('delete', *args, **kwargs)

    # Addresses API
    # -----------------------------------------------------------
    def get_addresses(self, **params):
        return self._get('v1', 'addresses', data=params)

    def get_address(self, address_id, **params):
        response = self._get('v1', 'addresses', address_id, data=params)
        return response

    def get_address_transactions(self, address_id, **params):
        response = self._get(
            'v1',
            'addresses', address_id,
            'transactions',
            data=params)
        return response

    def create_address(self):
        response = self._post('v1', 'addresses')
        return response

    def send(self, amount, address):
        params = {
            'amount': amount,
            'address': address
        }
        response = self._post('v1', 'addresses', 'send', data=params)
        return response
