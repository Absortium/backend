__author__ = 'andrew.shvv@gmail.com'

from decimal import Decimal as D

from absortium.model.models import Account
from absortium.tests.base import AbsoritumUnitTest
from core.utils.logging import getLogger

logger = getLogger(__name__)

from absortium import constants


class GeneralTest(AbsoritumUnitTest):
    def test_creation_mixin(self):
        accounts = Account.objects.all()
        self.assertEqual(len(accounts), len(constants.AVAILABLE_CURRENCIES))
        account = accounts[0]
        self.assertEqual(account.owner, self.user)

    def test_serialization(self, *args, **kwargs):
        account = self.get_account('btc')

        # Check that 'address' and 'btc' serialized properly
        self.assertEqual(account['currency'], 'btc')
        self.assertEqual(D(account['amount']), D("0.0"))


class PermissionTest(AbsoritumUnitTest):
    def test_try_delete(self, *args, **kwargs):
        with self.assertRaises(AssertionError):
            self.delete_account('btc')

    def test_with_amount(self):
        """
            Test that accounts could not be created with amount
        """

        # Accounts are creating during user creation, so delete all accounts
        accounts = Account.objects.all()
        accounts.delete()

        extra_data = {
            'amount': '10'
        }

        # Create btc account with amount
        self.create_account('btc', extra_data=extra_data)
        account = self.get_account('btc')
        self.assertEqual(D(account['amount']), D('0.0'))


class MalformedTest(AbsoritumUnitTest):
    def test_malformed_delete(self):
        # User trying to delete not created account
        with self.assertRaises(AssertionError):
            self.delete_account("19087698021")

    def test_malformed_retrieve(self):
        # User trying to delete not created account
        with self.assertRaises(AssertionError):
            self.get_account("19087698021", debug=True)
