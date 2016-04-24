__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED

from absortium.model.models import Account
from absortium.tests.base import AbsoritumUnitTest
from absortium.tests.mixins.coinbase import address
from core.utils.logging import getLogger

logger = getLogger(__name__)

from absortium import constants


class AccountTest(AbsoritumUnitTest):
    def test_creation_mixin(self):
        accounts = Account.objects.all()
        self.assertEqual(len(accounts), len(constants.AVAILABLE_CURRENCIES.keys()))
        account = accounts[0]
        self.assertEqual(account.owner, self.user)

    def test_serialization(self, *args, **kwargs):
        account_pk, account = self.get_account('btc')
        self.create_deposit(account_pk=account_pk)

        # Check that 'address' and 'btc' serialized properly
        self.assertEqual(account['address'], address)
        self.assertEqual(account['currency'], 'btc')

    def test_permissions(self, *args, **kwargs):
        account_pk, _ = self.get_account('btc')

        # User trying to delete account
        response = self.client.delete('/api/accounts/{pk}/'.format(pk=account_pk), format='json')
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

        # Create hacker user
        User = get_user_model()
        hacker = User(username="hacker")
        hacker.save()

        # Authenticate hacker
        self.client.force_authenticate(hacker)

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
