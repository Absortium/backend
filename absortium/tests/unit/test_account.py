__author__ = 'andrew.shvv@gmail.com'

from decimal import Decimal as D

from absortium.model.models import Account

from core.utils.logging import getLogger
from absortium.tests.base import AbsoritumUnitTest

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
        account = self.get_account('btc')

        with self.assertRaises(AssertionError):
            self.delete_account(pk=account['pk'])

    def test_access_foreign_account(self):
        account = self.get_account('btc')

        with self.assertRaises(AssertionError):
            self.retrieve_account(pk=account['pk'])

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
    def test_malformed(self):
        trash_account_pk = "19087698021"

        # User trying to delete not created account
        with self.assertRaises(AssertionError):
            self.delete_account(pk=trash_account_pk)
