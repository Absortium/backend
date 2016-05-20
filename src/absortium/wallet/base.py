__author__ = 'andrew.shvv@gmail.com'

from absortium import constants
from core.utils.logging import getLogger

logger = getLogger(__name__)

"""
Why we need such complexity - Function get_wallet_client() which returns instance of class BitcoinClient that actually
is wrapper around coinbase client?

1. There are a lot of bitcoin wallets, that is why I created BitcoinClient wrapper.
    1.1 Coinbase
    1.2 BlockChain
    and so on...
2. For testing purpose is better to have function that return class.
    2.1 Read 'mock' article http://www.voidspace.org.uk/python/mock/patch.html#where-to-patch
"""


class PostponeClient():
    """
        Class is used for postpone some class calls and execute it later.
    """

    def __init__(self, client, funcs):
        self.operations = []
        self.client = client
        self.funcs = funcs

    def do(self):
        for operation in self.operations:
            func = getattr(self.client, operation['func'])
            args = operation['args']
            kwargs = operation['kwargs']

            func(*args, **kwargs)

    def postpone(self, name):
        def wrapper(*args, **kwargs):
            self.operations.append({
                'func': name,
                'args': args,
                'kwargs': kwargs
            })

        return wrapper

    def __getattr__(self, item):
        attr = getattr(self.client, item)

        if item in self.funcs and callable(attr):
            return self.postpone(item)
        else:
            return attr


class Atomic():
    """
        Used for wrapping the original wallet client with PostponeClient
        and execute some calls only if non of exceptions was raised.
    """

    def __init__(self, funcs):
        self.clients = []

        if type(funcs) is not list:
            self.funcs = [funcs]
        else:
            self.funcs = funcs

    def __enter__(self):
        for currency in constants.AVAILABLE_CURRENCIES.values():
            client = get_wallet_client(currency)

            if not isinstance(client, PostponeClient):
                set_wallet_client(currency, PostponeClient(client=client,
                                                           funcs=self.funcs))
            else:
                raise Exception("Something went wrong - client already is PostponeClient")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for currency in constants.AVAILABLE_CURRENCIES.values():
            pclient = get_wallet_client(currency)

            if not exc_val:
                pclient.do()

            set_wallet_client(currency, pclient.client)


def atomic(*args, **kwargs):
    return Atomic(*args, **kwargs)


_clients = {
    constants.BTC: None,
    constants.ETH: None
}


def set_wallet_client(currency, client):
    global _clients
    _clients[currency] = client


def get_wallet_client(currency):
    global _clients
    if _clients[currency] is None:
        # import in this place was done because in 'test_wallet' test
        # we experienced some difficulties - we couldn't
        # mock currency client because it was imported before the mock patch

        if currency is constants.BTC:
            from absortium.wallet.bitcoin import BitcoinClient
            _clients[currency] = BitcoinClient()

        elif currency is constants.ETH:
            from absortium.wallet.ethereum import EthereumClient
            _clients[currency] = EthereumClient()
        else:
            raise Exception('There is no such wallet client')

    return _clients[currency]
