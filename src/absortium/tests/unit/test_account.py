__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED

from absortium.tests.base import AbsoritumUnitTest
from absortium.tests.mixins.account import CreateAccountMixin, address
from absortium.tests.mixins.deposit import CreateDepositMixin
from core.utils.logging import getLogger

logger = getLogger(__name__)


class AccountTest(AbsoritumUnitTest):
    def test_serialization(self, *args, **kwargs):
        account_pk = self.create_account(self.user, 'btc')
        self.create_deposit(self.user)

        response = self.client.get('/api/accounts/', format='json')
        account = self.get_first(response)

        # Check that 'address' and 'btc' serialized properly
        self.assertEqual(account['address'], address)
        self.assertEqual(account['currency'], 'btc')

    def test_permissions(self, *args, **kwargs):
        account_pk, _ = self.create_account(self.user, 'btc')

        # User trying to delete account
        response = self.client.delete('/api/accounts/{pk}/'.format(pk=account_pk), format='json')
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

        # Create hacker user
        User = get_user_model()
        hacker = User(username="hacker")
        hacker.save()

        # Authenticate hacker
        self.client.force_authenticate(hacker)

        # List all his accounts
        response = self.client.get('/api/accounts/', format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

        # Hacker trying access info of normal user account
        response = self.client.get('/api/accounts/{pk}/'.format(pk=account_pk), format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_malformed(self):
        trash_account_pk = "19087698021"

        # User trying to delete not created account
        response = self.client.delete('/api/accounts/{pk}/'.format(pk=trash_account_pk), format='json')
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

        # User trying to delete not created account
        response = self.client.get('/api/accounts/{pk}/'.format(pk=trash_account_pk), format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    # TODO test deposit notification
    def test_deposit(self):
        pass
