__author__ = 'andrew.shvv@gmail.com'

from mock import patch, Mock

from core.utils.logging import getLogger

logger = getLogger(__name__)


class BitcoinClientMockMixin():
    """
        BitcoinClientMockMixin substitute original bitcoin client and return mock btc addresses
    """

    def get_bitcoin_wallet_operations(self):
        return self._bitcoin_mock_wallet_client.operations

    def mock_bitcoin_client(self):
        # WARNING!: Be careful with names you may override variables in the class that inherit this mixin!

        self._bitcoin_mock_wallet_client = MockClient()
        self._bitcoin_client_patcher = patch('absortium.wallet.bitcoin.BitcoinClient',
                                             new=self._bitcoin_mock_wallet_client)
        self._bitcoin_client_patcher.start()

    def unmock_bitcoin_client(self):
        self._bitcoin_client_patcher.stop()


class MockClient(Mock):
    """
        Mock wallet client which rather than sends requests to the main server, collect it in 'operations' value.
    """
    operations = []

    def create_address(self, *args, **kwargs):
        self.operations.append({
            'func': 'create_address',
            'args': args,
            'kwargs': kwargs
        })

        from string import ascii_letters
        from random import choice
        s = ascii_letters + "0123456789"
        return "".join([choice(s) for _ in range(30)])

    def send(self, *args, **kwargs):
        self.operations.append({
            'func': 'send',
            'args': args,
            'kwargs': kwargs
        })
