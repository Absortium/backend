__author__ = 'andrew.shvv@gmail.com'
from rest_framework.status import HTTP_201_CREATED

from absortium.model.models import Withdrawal
from absortium.tests.mixins.lockmanager import LockManagerMixin
from absortium.tests.mixins.router import RouterMixin
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateWithdrawalMixin(RouterMixin, LockManagerMixin):
    def create_withdrawal(self, user, amount="0.00001", with_authentication=True, with_checks=True, account_pk=None):
        data = {
            'amount': amount,
            'address': '1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX'
        }

        if with_authentication:
            # Authenticate normal user
            # TODO: now it is usual user but then we should change it to notification service user!!
            self.client.force_authenticate(user)

        if not account_pk:
            # Get list of accounts
            # TODO: now get account lists but then notification server will search account by address given in notification from coinbase!!
            response = self.client.get('/api/accounts/', format='json')
            account = self.get_first(response)
            account_pk = account['pk']

        # Create withdrawal
        url = '/api/accounts/{account_pk}/withdrawals/'.format(account_pk=account_pk)
        response = self.client.post(url, data=data, format='json')

        if with_checks:
            self.assertEqual(response.status_code, HTTP_201_CREATED)
            task_id = response.json()['task_id']

            # Get the publishment that we sent to the router
            publishment = self.get_publishment_by_task_id(topic=user.pk, task_id=task_id)
            self.assertNotEqual(publishment, None)

            self.assertEqual(publishment["status"], "SUCCESS")
            withdrawal_pk = publishment["data"]["pk"]

            # Check that withdrawal exist in db
            try:
                withdrawal = Withdrawal.objects.get(pk=withdrawal_pk)
            except Withdrawal.DoesNotExist:
                self.fail("Withdrawal object wasn't found in db")

            # Check that withdrawal belongs to an account
            self.assertEqual(withdrawal.account.pk, account_pk)

            return withdrawal_pk, withdrawal
