# coding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import warnings

import requests

from .auth import HMACAuth
from .compat import imap, urljoin, quote
from .error import build_api_error
from .model import APIObject, Address, new_api_object
from .util import check_uri_security, encode_params

ETHCLIENT_CRT_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'ca-ethclient.crt')

ETHCLIENT_CALLBACK_PUBLIC_KEY_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'ethclient-callback.pub')


class Client(object):
    """ API Client for the ethclient API.

    Entry point for making requests to the ethclient API. Provides helper methods
    for common API endpoints, as well as niceties around response verification
    and formatting.

    Any errors will be raised as exceptions. These exceptions will always be
    subclasses of `ethclient.error.APIError`. HTTP-related errors will also be
    subclasses of `requests.HTTPError`.

    Full API docs, including descriptions of each API and its paramters, are
    available here: https://developers.ethclient.com/api
    """
    VERIFY_SSL = True

    BASE_API_URI = 'http://docker.ethclient'
    API_VERSION = '2016-05-17'

    cached_callback_public_key = None

    def __init__(self, api_key, api_secret, base_api_uri=None, api_version=None):
        if not api_key:
            raise ValueError('Missing `api_key`.')
        if not api_secret:
            raise ValueError('Missing `api_secret`.')

        # Allow passing in a different API base.
        self.BASE_API_URI = check_uri_security(base_api_uri or self.BASE_API_URI)

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
                                'User-Agent': 'ethclient/python/3.0'})
        return session

    def _create_api_uri(self, *parts):
        """Internal helper for creating fully qualified endpoint URIs."""
        return urljoin(self.BASE_API_URI, '/'.join(imap(quote, parts)))

    def _request(self, method, *relative_path_parts, **kwargs):
        """Internal helper for creating HTTP requests to the ethclient API.

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
        return self._handle_response(response)

    def _handle_response(self, response):
        """Internal helper for handling API responses from the ethclient server.

        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        if not str(response.status_code).startswith('2'):
            raise build_api_error(response)
        return response

    def _get(self, *args, **kwargs):
        return self._request('get', *args, **kwargs)

    def _post(self, *args, **kwargs):
        return self._request('post', *args, **kwargs)

    def _put(self, *args, **kwargs):
        return self._request('put', *args, **kwargs)

    def _delete(self, *args, **kwargs):
        return self._request('delete', *args, **kwargs)

    def _make_api_object(self, response, model_type=None):
        blob = response.json()
        data = blob.get('data', None)
        # All valid responses have a "data" key.
        if data is None:
            raise build_api_error(response, blob)
        # Warn the user about each warning that was returned.
        warnings_data = blob.get('warnings', None)
        for warning_blob in warnings_data or []:
            message = "%s (%s)" % (
                warning_blob.get('message', ''),
                warning_blob.get('url', ''))
            warnings.warn(message, UserWarning)

        pagination = blob.get('pagination', None)
        kwargs = {
            'response': response,
            'pagination': pagination and new_api_object(None, pagination, APIObject),
            'warnings': warnings_data and new_api_object(None, warnings_data, APIObject),
        }
        if isinstance(data, dict):
            obj = new_api_object(self, data, model_type, **kwargs)
        else:
            obj = APIObject(self, **kwargs)
            obj.data = new_api_object(self, data, model_type)
        return obj

    # Addresses API
    # -----------------------------------------------------------
    def get_addresses(self, **params):
        """https://developers.ethclient.com/api/v2#list-addresses"""
        response = self._get('v2', 'addresses', data=params)
        return self._make_api_object(response, Address)

    def get_address(self, address_id, **params):
        """https://developers.ethclient.com/api/v2#show-addresss"""
        response = self._get('v2', 'addresses', address_id, data=params)
        return self._make_api_object(response, Address)

    def get_address_transactions(self, account_id, address_id, **params):
        """https://developers.ethclient.com/api/v2#list-address39s-transactions"""
        response = self._get(
            'v2',
            'addresses', address_id,
            'transactions',
            data=params)
        return self._make_api_object(response, Transaction)

    def create_address(self, account_id, **params):
        """https://developers.ethclient.com/api/v2#create-address"""
        response = self._post('v2', 'addresses', data=params)
        return self._make_api_object(response, Address)

    def send(self):
        pass
