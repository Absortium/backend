from absortium.utils import eth2wei

__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED

from absortium.tests.base import AbsoritumUnitTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class DepositTest(AbsoritumUnitTest):
    def test_precision(self, *args, **kwargs):
        account = self.get_account('btc')
        self.make_deposit(account, "10")
        self.check_account_amount(account, "10")

    def test_smaller_than_min(self):
        account = self.get_account('btc')
        with self.assertRaises(AssertionError):
            self.make_deposit(account, "0.000000001")

    def test_permissions(self, *args, **kwargs):
        account = self.get_account('btc')
        deposit_pk, _ = self.make_deposit(account)

        # Create hacker user
        User = get_user_model()
        hacker = User(username="hacker")
        hacker.save()

        # Authenticate hacker
        self.client.force_authenticate(hacker)

        # Try to get deposits from another account
        url = '/api/accounts/{account_pk}/deposits/'.format(account_pk=account['pk'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to get deposit info from another account
        url = '/api/accounts/{account_pk}/deposits/{deposit_pk}/'.format(account_pk=account['pk'],
                                                                         deposit_pk=deposit_pk)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to delete deposit from another account
        # TODO: this operation should not be granted at all
        url = '/api/accounts/{account_pk}/deposits/{deposit_pk}/'.format(account_pk=account['pk'],
                                                                         deposit_pk=deposit_pk)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

    def test_malformed(self, *args, **kwargs):
        trash_account_pk = "129381728763"
        trash_deposit_pk = "972368423423"

        # Try to get deposit info from uncreated account
        url = '/api/accounts/{account_pk}/deposits/{deposit_pk}/'.format(account_pk=trash_account_pk,
                                                                         deposit_pk=trash_deposit_pk)

        # Create an account and try to get uncreated deposit
        account = self.get_account('btc')
        url = '/api/accounts/{account_pk}/deposits/{deposit_pk}/'.format(account_pk=account['pk'],
                                                                         deposit_pk=trash_deposit_pk)

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
