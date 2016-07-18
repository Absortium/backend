__author__ = 'andrew.shvv@gmail.com'

from mock import patch, Mock

from core.utils.logging import getLogger

logger = getLogger(__name__)

operations = []


class EthereumClientMockMixin():
    """
        EthereumClientMockMixin substitute original ethereum client and return mock eth addresses
    """

    def flush_ethereum_client_operations(self):
        global operations
        operations = []

    def get_ethereum_wallet_operations(self):
        global operations
        return operations

    def mock_ethereum_client(self):
        # WARNING!: Be careful with names you may override variables in the class that inherit this mixin!

        self._ethereum_mock_wallet_client = MockClient()
        self._ethereum_client_patcher = patch('absortium.wallet.ethereum.EthereumClient',
                                              new=self._ethereum_mock_wallet_client)
        self._ethereum_client_patcher.start()

    def unmock_ethereum_client(self):
        self._ethereum_client_patcher.stop()


class MockClient(Mock):
    """
        Mock wallet client which rather than sends requests to the main server, collect it in 'operations' value.
    """

    def create_address(self, *args, **kwargs):
        global operations

        operations.append({
            'func': 'create_address',
            'args': args,
            'kwargs': kwargs
        })

        from string import ascii_letters
        from random import choice
        s = ascii_letters + "0123456789"
        return "".join([choice(s) for _ in range(30)])

    def send(self, *args, **kwargs):
        global operations

        operations.append({
            'func': 'send',
            'args': args,
            'kwargs': kwargs
        })
