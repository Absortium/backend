__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED

from absortium.model.models import Deposit
from absortium.tests.mixins.lockmanager import LockManagerMixin
from absortium.tests.mixins.router import RouterMixin
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateDepositMixin(RouterMixin, LockManagerMixin):
    def create_deposit(self, user, amount="0.00001", with_checks=True, with_authentication=True, account_pk=None):
        data = {
            'amount': amount
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

        # Create deposit
        url = '/api/accounts/{account_pk}/deposits/'.format(account_pk=account_pk)
        response = self.client.post(url, data=data, format='json')

        if with_checks:
            self.assertEqual(response.status_code, HTTP_201_CREATED)
            task_id = response.json()['task_id']

            # Get the publishment that we sent to the router
            publishment = self.get_publishment_by_task_id(topic=user.pk, task_id=task_id)
            self.assertNotEqual(publishment, None)

            self.assertEqual(publishment["status"], "SUCCESS")
            deposit_pk = publishment["data"]["pk"]

            # Check that deposit exist in db
            try:
                deposit = Deposit.objects.get(pk=deposit_pk)
            except Deposit.DoesNotExist:
                self.fail("Deposit object wasn't found in db")

            # Check that deposit belongs to an account
            self.assertEqual(deposit.account.pk, account_pk)

            return deposit_pk, deposit
