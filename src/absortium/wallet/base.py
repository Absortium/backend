__author__ = 'andrew.shvv@gmail.com'

from absortium import constants
from absortium.wallet.bitcoin import BitcoinClient
from absortium.wallet.ethereum import EthereumClient

_clients = {
    constants.BTC: None,
    constants.ETH: None
}

"""
Why we need such complexity - Function get_client() which returns instance of class BitcoinClient that actually
is wrapper around coinbase client?

1. There are a lot of bitcoin wallets, that is why I created BitcoinClient wrapper.
    1.1 Coinbase
    1.2 BlockChain
    and so on...
2. For testing purpose is better to have function that return class.
    2.1 Read 'mock' article http://www.voidspace.org.uk/python/mock/patch.html#where-to-patch
"""


def get_client(currency):
    global _clients
    if _clients[currency] is None:
        if currency is constants.BTC:
            _clients[currency] = BitcoinClient()
        elif currency is constants.ETH:
            _clients[currency] = EthereumClient()
        else:
            raise Exception('There is no such wallet client')

    return _clients[currency]
