__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED

from absortium.model.models import Deposit
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateDepositMixin():
    def create_deposit(self, account_pk, amount="0.00001", with_checks=True, user=None):
        data = {
            'amount': amount
        }

        if user:
            # Authenticate normal user
            # TODO: now it is usual user but then we should change it to notification service user!!
            self.client.force_authenticate(user)

        # Create deposit
        url = '/api/accounts/{account_pk}/deposits/'.format(account_pk=account_pk)
        response = self.client.post(url, data=data, format='json')

        if with_checks:
            self.assertEqual(response.status_code, HTTP_201_CREATED)
            task_id = response.json()['task_id']

            # Get the publishment that we sent to the router
            # TODO: This is not good when one mixin depends of methods of another (RouterMixin)
            publishment = self.get_publishment_by_task_id(task_id=task_id)
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
