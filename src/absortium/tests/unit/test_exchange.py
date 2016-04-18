__author__ = "andrew.shvv@gmail.com"

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED

from absortium.tests.base import AbsoritumUnitTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class ExchangeTest(AbsoritumUnitTest):
    def setUp(self):
        super().setUp()

        self.primary_btc_account_pk, _ = self.create_account("btc")
        self.primary_eth_account_pk, _ = self.create_account("eth")

        self.create_deposit(self.primary_btc_account_pk, amount="10.0")

        # Create some another user
        User = get_user_model()
        some_user = User(username="some_user")
        some_user.save()

        self.some_user = some_user

        # Authenticate some another user
        self.client.force_authenticate(self.some_user)

        self.some_eth_account_pk, _ = self.create_account("eth")
        self.some_btc_account_pk, _ = self.create_account("btc")

        self.create_deposit(self.some_eth_account_pk, amount="20.0")

        self.client.force_authenticate(self.user)

    def test_permissions(self, *args, **kwargs):
        exchange_pk, _ = self.create_exchange(self.primary_btc_account_pk, currency="eth", status="INIT")

        # Create hacker user
        User = get_user_model()
        hacker = User(username="hacker")
        hacker.save()

        # Authenticate hacker
        self.client.force_authenticate(hacker)

        # Try to get exchanges from another account
        url = "/api/accounts/{account_pk}/exchanges/".format(account_pk=self.primary_btc_account_pk)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to create exchange in another account
        data = {
            "currency": "btc",
            "amount": "0.0111",
            "price": "111"
        }
        url = "/api/accounts/{account_pk}/exchanges/".format(account_pk=self.primary_btc_account_pk)
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to get exchange info from another account
        url = "/api/accounts/{account_pk}/exchanges/{exchange_pk}/".format(account_pk=self.primary_btc_account_pk,
                                                                           exchange_pk=exchange_pk)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to delete exchange from another account
        url = "/api/accounts/{account_pk}/exchanges/{exchange_pk}/".format(account_pk=self.primary_btc_account_pk,
                                                                           exchange_pk=exchange_pk)
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

    def test_malformed(self, *args, **kwargs):
        trash_account_pk = "129381728763"
        trash_exchange_pk = "972368423423"

        # Try to get exchange info from uncreated account
        url = "/api/accounts/{account_pk}/exchanges/{exchange_pk}/".format(account_pk=trash_account_pk,
                                                                           exchange_pk=trash_exchange_pk)

        # Create an account and try to get uncreated exchange
        account_pk, _ = self.create_account("btc")
        url = "/api/accounts/{account_pk}/exchanges/{exchange_pk}/".format(account_pk=account_pk,
                                                                           exchange_pk=trash_exchange_pk)

        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    # TODO: Create test that checks incorrect primary, secondary currency, price, amount etc
    def test_malformed_data(self):
        malformed_amount = "(*YGV*T^C%D"
        with self.assertRaises(AssertionError):
            self.create_exchange(self.primary_btc_account_pk, currency="eth", price="2.0", amount=malformed_amount,
                                 status="INIT")

        malformed_currency = "(*YGV*T^C%D"
        with self.assertRaises(AssertionError):
            self.create_exchange(self.primary_btc_account_pk, currency=malformed_currency, price="2.0", amount="1.0",
                                 status="INIT")

        malformed_price = "(*YGV*T^C%D"
        with self.assertRaises(AssertionError):
            self.create_exchange(self.primary_btc_account_pk, currency="eth", price=malformed_price, amount="1.0",
                                 status="INIT")

    def test_creation(self):
        self.create_exchange(self.primary_btc_account_pk, currency="eth", price="2.0", amount="3.0", status="INIT")

        self.check_account_amount(self.primary_btc_account_pk, amount="7.0")
        self.check_account_amount(self.primary_eth_account_pk, amount="0.0")

    def test_run_out_deposit(self):
        self.create_exchange(self.primary_btc_account_pk, currency="eth", price="2.0", amount="999", status="REJECTED")

        self.check_account_amount(self.primary_btc_account_pk, amount="10.0")
        self.check_account_amount(self.primary_eth_account_pk, amount="0.0")

    def test_exchange_completed(self):
        self.create_exchange(self.primary_btc_account_pk, currency="eth", price="2.0", amount="5.0", status="INIT")
        self.create_exchange(self.primary_btc_account_pk, currency="eth", price="2.0", amount="5.0", status="INIT")

        self.client.force_authenticate(self.some_user)
        self.create_exchange(self.some_eth_account_pk, currency="btc", price="0.5", amount="20.0")

        self.check_account_amount(self.some_btc_account_pk, amount="10.0")
        self.check_account_amount(self.some_eth_account_pk, amount="0.0")

        self.client.force_authenticate(self.user)
        self.check_account_amount(self.primary_btc_account_pk, amount="0.0")
        self.check_account_amount(self.primary_eth_account_pk, amount="20.0")

    def test_exchange_pending(self):
        self.create_exchange(self.primary_btc_account_pk, currency="eth", price="2.0", amount="8.0", status="INIT")
        self.check_account_amount(self.primary_btc_account_pk, amount="2.0")

        self.client.force_authenticate(self.some_user)
        self.create_exchange(self.some_eth_account_pk, currency="btc", price="0.5", amount="20.0", status="PENDING")
        self.check_account_amount(self.some_eth_account_pk, amount="0.0")
        self.check_account_amount(self.some_btc_account_pk, amount="8.0")

        self.client.force_authenticate(self.user)
        self.check_account_amount(self.primary_btc_account_pk, amount="2.0")
        self.check_account_amount(self.primary_eth_account_pk, amount="16.0")
