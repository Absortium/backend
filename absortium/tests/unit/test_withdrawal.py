__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_404_NOT_FOUND

from core.utils.logging import getLogger
from absortium.tests.base import AbsoritumUnitTest

logger = getLogger(__name__)


class WithdrawalTest(AbsoritumUnitTest):
    def setUp(self):
        super().setUp()

        self.flush_bitcoin_client_operations()
        self.flush_ethereum_client_operations()

    def test_precision_btc(self, *args, **kwargs):
        account = self.get_account('btc')
        self.make_deposit(account, "10")
        self.make_withdrawal(account, "10")
        self.check_account_amount(account, "0")

        self.make_deposit(account, "0.1")
        self.make_withdrawal(account, "0.1")
        self.check_account_amount(account, "0")

    def test_precision_eth(self, *args, **kwargs):
        account = self.get_account('eth')
        self.make_deposit(account, "10")
        self.make_withdrawal(account, "10")
        self.check_account_amount(account, "0")

        self.make_deposit(account, "0.1")
        self.make_withdrawal(account, "0.1")
        self.check_account_amount(account, "0")

    def test_smaller_than_min(self):
        account = self.get_account('btc')
        self.make_deposit(account, "1")
        with self.assertRaises(AssertionError):
            self.make_withdrawal(account, "0.000000001")

    def test_permissions(self, *args, **kwargs):
        account = self.get_account('btc')
        self.make_deposit(account)
        withdrawal = self.make_withdrawal(account)

        # Create hacker user
        User = get_user_model()
        hacker = User(username="hacker")
        hacker.save()

        # Authenticate hacker
        self.client.force_authenticate(hacker)

        # Try to get withdrawal info from another account
        url = '/api/withdrawals/{pk}/'.format(pk=withdrawal['pk'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_withdrawal_without_money(self):
        account = self.get_account('btc')
        with self.assertRaises(AssertionError):
            self.make_withdrawal(account)

    def test_malformed(self, *args, **kwargs):
        account = self.get_account('btc')

        malformed_amount = "asdmnajsid"
        with self.assertRaises(AssertionError):
            self.make_withdrawal(account, amount=malformed_amount)

        malformed_amount = "-1"
        with self.assertRaises(AssertionError):
            self.make_withdrawal(account, amount=malformed_amount)

    def test_send_btc(self, *args, **kwargs):
        account = self.get_account('btc')
        self.make_deposit(account, "10")
        self.make_withdrawal(account, "10")
        self.check_account_amount(account, "0")

        self.assertEqual(len(self.get_bitcoin_wallet_operations()), 1)

    def test_send_eth(self, *args, **kwargs):
        account = self.get_account('eth')
        self.make_deposit(account, "10")
        self.make_withdrawal(account, "10")
        self.check_account_amount(account, "0")

        self.assertEqual(len(self.get_ethereum_wallet_operations()), 1)
