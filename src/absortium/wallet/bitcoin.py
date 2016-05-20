__author__ = 'andrew.shvv@gmail.com'

from coinbase.wallet.client import Client
from coinbase.wallet.error import NotFoundError
from django.contrib.auth import settings

from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


class BitcoinClient():
    _client = None

    @property
    def client(self):
        if self._client is None:
            self._client = Client(api_key=settings.COINBASE_API_KEY,
                                  api_secret=settings.COINBASE_API_SECRET,
                                  base_api_uri=settings.COINBASE_API_URL)
            if settings.COINBASE_SANDBOX:
                def mock_verify_callback(*args, **kwargs):
                    return True

                self._client.verify_callback = mock_verify_callback

        return self._client

    def create_address(self):
        try:
            response = self.client.create_address(account_id=settings.COINBASE_ACCOUNT_ID)
            coinbase_data = response['data']
            return coinbase_data['address']
        except NotFoundError as e:
            logger.debug(e)

    def send(self, amount, address):
        pass
