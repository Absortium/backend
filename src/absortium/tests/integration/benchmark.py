__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_405_METHOD_NOT_ALLOWED

from absortium.tests.base import AbsortiumTest
from absortium.tests.mixins.account import CreateAccountMixin
from absortium.tests.mixins.deposit import CreateDepositMixin
from absortium.tests.mixins.withdrawal import CreateWithdrawalMixin
from core.utils.logging import getLogger

logger = getLogger(__name__)


class DepositTest(AbsortiumTest, CreateDepositMixin, CreateAccountMixin, CreateWithdrawalMixin):
    def test_permissions(self, *args, **kwargs):


        self.create_account(self.user, 'btc', with_authentication=False, with_checks=False)


        self.create_deposit(self.user, with_authentication=False, with_checks=False)
        self.create_withdrawal(self.user, with_authentication=False, with_checks=False)

