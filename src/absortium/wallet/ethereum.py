__author__ = 'andrew.shvv@gmail.com'

from django.conf import settings


class EthereumClient():
    url = settings.ETHCLIENT_URL

    def create_address(self):
        from string import ascii_letters
        from random import choice
        s = ascii_letters + "0123456789"
        return "".join([choice(s) for _ in range(30)])
