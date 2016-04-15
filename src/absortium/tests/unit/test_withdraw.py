__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED

from absortium.tests.base import AbsortiumTest
from absortium.tests.mixins.account import CreateAccountMixin
from absortium.tests.mixins.deposit import CreateDepositMixin
from absortium.tests.mixins.withdrawal import CreateWithdrawalMixin
from core.utils.logging import getLogger

logger = getLogger(__name__)


class WithdrawalTest(AbsortiumTest, CreateWithdrawalMixin, CreateAccountMixin, CreateDepositMixin):
    def test_permissions(self, *args, **kwargs):
        account_pk, _ = self.create_account(self.user, 'btc')
        self.create_deposit(self.user)
        withdrawal_pk, _ = self.create_withdrawal(self.user)

        # Create hacker user
        User = get_user_model()
        hacker = User(username="hacker")
        hacker.save()

        # Authenticate hacker
        self.client.force_authenticate(hacker)

        # Try to get withdrawals from another account
        url = '/api/accounts/{account_pk}/withdrawals/'.format(account_pk=account_pk)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to create withdrawal in another account
        # TODO: this operation should be granted only for notification service
        data = {
            'amount': '0.0111',
        }
        url = '/api/accounts/{account_pk}/withdrawals/'.format(account_pk=account_pk)
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to get withdrawal info from another account
        url = '/api/accounts/{account_pk}/withdrawals/{withdrawal_pk}/'.format(account_pk=account_pk,
                                                                               withdrawal_pk=withdrawal_pk)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to delete withdrawal from another account
        # TODO: this operation should be granted at all
        url = '/api/accounts/{account_pk}/withdrawals/{withdrawal_pk}/'.format(account_pk=account_pk,
                                                                               withdrawal_pk=withdrawal_pk)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

    def test_malformed(self, *args, **kwargs):
        trash_account_pk = "129381728763"
        trash_withdrawal_pk = "972368423423"

        # Try to get withdrawal info from uncreated account
        url = '/api/accounts/{account_pk}/withdrawals/{withdrawal_pk}/'.format(account_pk=trash_account_pk,
                                                                               withdrawal_pk=trash_withdrawal_pk)

        # Create an account and try to get uncreated withdrawal
        account_pk, _ = self.create_account(self.user, 'btc')
        url = '/api/accounts/{account_pk}/withdrawals/{withdrawal_pk}/'.format(account_pk=account_pk,
                                                                               withdrawal_pk=trash_withdrawal_pk)

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_malformed_amount_price(self):
        account_pk, _ = self.create_account(self.user, 'btc')

        with self.assertRaises(AssertionError):
            self.create_withdrawal(self.user, amount="asdmnajsid")
