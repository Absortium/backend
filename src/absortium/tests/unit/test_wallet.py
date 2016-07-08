from absortium.wallet.pool import AccountPool

__author__ = "andrew.shvv@gmail.com"

from absortium import constants, wallet
from absortium.tests.base import AbsoritumUnitTest
from absortium.wallet.base import get_wallet_client
from absortium.celery import tasks
from core.utils.logging import getLogger

logger = getLogger(__name__)


class WalletAtomicTest(AbsoritumUnitTest):
    def test_publishments_atomic_with_exception(self):
        """
            Check publishemnt.atomic context manager. If exception was raised inside the block
            than publishments should not be published.
        """

        try:
            with wallet.atomic(funcs=["send"]):
                btc_client = get_wallet_client(constants.BTC)
                ba1 = btc_client.create_address()
                ba2 = btc_client.create_address()
                btc_client.send(amount="100", from_address=ba1, to_address=ba2)

                eth_client = get_wallet_client(constants.ETH)
                ea1 = eth_client.create_address()
                ea2 = eth_client.create_address()
                eth_client.send(amount="200", from_address=ea1, to_address=ea2)
                raise Exception("Something wrong!")
        except Exception:
            # Check that if exception was raised 'send' operation wasn't executed
            self.assertNotIn('send', [operation['func'] for operation in self.get_bitcoin_wallet_operations()])
            self.assertNotIn('send', [operation['func'] for operation in self.get_ethereum_wallet_operations()])

    def test_publishments_atomic_without_exception(self):
        """
            Check publishemnt.atomic context manager. If exception was raised inside the block
            than publishments should not be published.
        """

        with wallet.atomic(funcs=["send"]):
            btc_client = get_wallet_client(constants.BTC)
            ba1 = btc_client.create_address()
            ba2 = btc_client.create_address()
            btc_client.send(amount="100", from_address=ba1, to_address=ba2)

            eth_client = get_wallet_client(constants.ETH)
            ea1 = eth_client.create_address()
            ea2 = eth_client.create_address()
            eth_client.send(amount="200", from_address=ea1, to_address=ea2)

            self.assertNotIn('send', [operation['func'] for operation in self.get_bitcoin_wallet_operations()])
            self.assertNotIn('send', [operation['func'] for operation in self.get_ethereum_wallet_operations()])

        # Check that if exception was raised 'send' operation wasn't executed
        self.assertIn('send', [operation['func'] for operation in self.get_bitcoin_wallet_operations()])
        self.assertIn('send', [operation['func'] for operation in self.get_ethereum_wallet_operations()])

    def test_account_pregeneration(self):
        """
            Test pool account pregeneration.
        """

        tasks.pregenerate_accounts()
        currencies = constants.AVAILABLE_CURRENCIES

        for currency in currencies:
            count = constants.ACCOUNT_POOL_LENGTH - len(AccountPool(currency))
            self.assertEqual(count, 0)
