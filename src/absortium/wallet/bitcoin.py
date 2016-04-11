__author__ = 'andrew.shvv@gmail.com'

from coinbase.wallet.client import Client
from django.contrib.auth import settings

_client = None


def get_coinbase_client():
    global _client
    if _client is None:
        _client = Client(api_key=settings.COINBASE_API_KEY,
                         api_secret=settings.COINBASE_API_SECRET,
                         base_api_uri=settings.COINBASE_API_URL)
        if settings.COINBASE_SANDBOX:
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


def create_address(account_id):
    client = get_coinbase_client()
    return client.create_address(account_id=account_id)
