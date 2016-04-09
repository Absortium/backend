__author__ = 'andrew.shvv@gmail.com'

from coinbase.wallet.client import Client
from flask import current_app as app

_client = None


def get_coinbase_client():
    global _client
    if _client is None:
        _client = Client(api_key=app.config['COINBASE_API_KEY'],
                         api_secret=app.config['COINBASE_API_SECRET'],
                         base_api_uri=app.config['COINBASE_API_URL'])
        if app.config['COINBASE_SANDBOX']:
            def mock_verify_callback(*args, **kwargs):
                return True

            _client.verify_callback = mock_verify_callback

    return _client


_primary_account = None


def get_primary_account():
    global _primary_account
    if _primary_account is None:
        client = get_coinbase_client()
        _primary_account = client.get_primary_account()
    return _primary_account
