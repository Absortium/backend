__author__ = 'andrew.shvv@gmail.com'

from django.conf import settings

from core.utils.logging import getPrettyLogger
from ethwallet.client import Client
from ethwallet.error import NotFoundError

logger = getPrettyLogger(__name__)

_client = None


class EthereumClient():
    _client = None

    @property
    def client(self):
        if self._client is None:
            self._client = Client(api_key=settings.ETHWALLET_API_KEY,
                                  api_secret=settings.ETHWALLET_API_SECRET,
                                  base_api_uri=settings.ETHWALLET_URL)
        return self._client

    def create_address(self):
        try:
            response = self.client.create_address()
            return response['address']
        except NotFoundError as e:
            logger.debug(e)

    def send(self, amount, address):
        self.client.send(amount, address)
