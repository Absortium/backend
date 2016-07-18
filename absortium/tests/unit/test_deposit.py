from absortium import constants

__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_404_NOT_FOUND

from absortium.tests.base import AbsoritumUnitTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class DepositTest(AbsoritumUnitTest):
    def test_precision_btc(self, *args, **kwargs):
        account = self.get_account('btc')
        self.make_deposit(account, "10")
        self.check_account_amount(account, "10")

    def test_precision_eth(self, *args, **kwargs):
        account = self.get_account('eth')
        self.make_deposit(account, "10")
        self.check_account_amount(account, "10")

    def test_accuracy(self, *args, **kwargs):
        account = self.get_account('eth')

        amount = "1" * (constants.MAX_DIGITS - constants.DECIMAL_PLACES) + "." + "2" * constants.DECIMAL_PLACES
        self.make_deposit(account, amount)
        self.check_account_amount(account, amount)

    def test_permissions(self, *args, **kwargs):
        deposit = self.make_deposit(self.get_account('btc'))

        # Create hacker user
        User = get_user_model()
        hacker = User(username="hacker")
        hacker.save()

        # Authenticate hacker
        self.client.force_authenticate(hacker)

        # Try to delete deposit from another account
        # TODO: this operation should not be granted at all
        url = '/api/deposits/{pk}/'.format(pk=deposit['pk'])

        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_malformed(self, *args, **kwargs):
        trash_pk = "972368423423"

        # Create an account and try to get uncreated deposit
        account = self.get_account('btc')
        url = '/api/deposits/{pk}/'.format(pk=trash_pk)

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_malformed_amount_price(self):
        account = self.get_account('btc')
        malformed_amount = "*asa1&^*%^&$*%EOP"

        # Create deposit should assert if deposit response code is not 200
        with self.assertRaises(AssertionError):
            self.make_deposit(account, amount=malformed_amount)

        malformed_amount = "-1"
        with self.assertRaises(AssertionError):
            self.make_deposit(account, amount=malformed_amount)
