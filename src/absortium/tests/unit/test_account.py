__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED

from absortium.model.models import Account
from absortium.tests.base import AbsoritumUnitTest
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
        account = self.get_account('btc')
        self.make_deposit(account)

        # Check that 'address' and 'btc' serialized properly
        self.assertEqual(account['currency'], 'btc')
        self.assertEqual(account['amount'], 0)

    def test_permissions(self, *args, **kwargs):
        account = self.get_account('btc')
        # User trying to delete account
        response = self.client.delete('/api/accounts/{pk}/'.format(pk=account['pk']), format='json')
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

        # Create hacker user
        User = get_user_model()
        hacker = User(username="hacker")
        hacker.save()

        # Authenticate hacker
        self.client.force_authenticate(hacker)

        # Hacker trying access info of normal user account
        response = self.client.get('/api/accounts/{pk}/'.format(pk=account['pk']), format='json')
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
