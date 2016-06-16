__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model

from absortium.tests.base import AbsoritumUnitTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class HistoryTest(AbsoritumUnitTest):
    def setUp(self):
        super().setUp()

        self.primary_btc_account = self.get_account("btc")
        self.primary_eth_account = self.get_account("eth")

        self.make_deposit(self.primary_btc_account, amount="10.0")
        self.check_account_amount(self.primary_btc_account, amount="10.0")

        # Create some another user
        User = get_user_model()
        some_user = User(username="some_user")
        some_user.save()

        self.some_user = some_user

        # Authenticate some another user
        self.client.force_authenticate(self.some_user)

        self.some_eth_account = self.get_account("eth")
        self.some_btc_account = self.get_account("btc")

        self.make_deposit(self.some_eth_account, amount="20.0")
        self.check_account_amount(self.some_eth_account, amount="20.0")

        self.client.force_authenticate(self.user)

    def test_exchanges_count(self):
        """
            Check that we get only exchanges which belong to the user.
        """
        self.create_exchange(price="1", amount="1", status="init")
        self.create_exchange(price="1", amount="1", status="init")
        self.assertEqual(len(self.get_exchanges_history()), 0)

        self.client.force_authenticate(self.some_user)
        self.create_exchange(from_currency="eth", to_currency="btc", price="1", amount="2", status="completed")

        self.assertEqual(len(self.get_exchanges_history()), 4)
        self.assertEqual(len(self.get_exchanges_history("btc", "eth")), 2)
        self.assertEqual(len(self.get_exchanges_history("eth", "btc")), 2)
