__author__ = 'andrew.shvv@gmail.com'

from mock import patch

from core.utils.logging import getLogger

logger = getLogger(__name__)


def get_address(*args, **kwargs):
    from string import ascii_letters
    from random import choice
    s = ascii_letters + "0123456789"
    return "".join([choice(s) for _ in range(30)])


class CoinbaseMockMixin():
    """
        CoinbaseMockMixin substitute original coinbase client and return mock btc/eth addresses
    """

    def __init__(self):
        # WARNING!: Be careful with names you may override variables in the class that inherit this mixin!
        self._coinbase_patcher = None

    def mock_coinbase(self):
        self._coinbase_patcher = patch('absortium.wallet.bitcoin.BitcoinClient.create_address', new=get_address)
        self.mock_client = self._coinbase_patcher.start()

    def unmock_coinbase(self):
        self._coinbase_patcher.stop()
