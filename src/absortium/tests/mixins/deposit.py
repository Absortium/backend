__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from absortium.model.models import Deposit
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


class CreateDepositMixin():
    def make_deposit(self, account, amount="99999", with_checks=True, user=None, debug=False):
        data = {
            'amount': amount
        }

        if user:
            # Authenticate normal user
            # TODO: now it is usual user but then we should change it to notification service user!!
            self.client.force_authenticate(user)

        # Create deposit
        url = '/api/accounts/{account_pk}/deposits/'.format(account_pk=account['pk'])
        response = self.client.post(url, data=data, format='json')

        self.assertIn(response.status_code, [HTTP_201_CREATED, HTTP_204_NO_CONTENT])

        if debug:
            logger.info(response.content)

        if with_checks:
            deposit = response.json()

            # Check that deposit exist in db
            try:
                obj = Deposit.objects.get(pk=deposit['pk'])
            except Deposit.DoesNotExist:
                self.fail("Deposit object wasn't found in db")

            # Check that deposit belongs to an account
            self.assertEqual(obj.account.pk, account['pk'])

            return deposit['pk'], obj
