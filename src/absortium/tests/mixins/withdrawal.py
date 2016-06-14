from absortium.utils import convert

__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from absortium.model.models import Withdrawal
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateWithdrawalMixin():
    def make_withdrawal(self, account, amount="0.00001", user=None, with_checks=True, debug=False):
        data = {
            'amount': convert(amount),
            'address': '1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX'
        }

        if user:
            # Authenticate normal user
            # TODO: now it is usual user but then we should change it to notification service user!!
            self.client.force_authenticate(user)

        # Create withdrawal
        url = '/api/accounts/{account_pk}/withdrawals/'.format(account_pk=account['pk'])
        response = self.client.post(url, data=data, format='json')

        if debug:
            logger.debug(response.content)

        self.assertIn(response.status_code, [HTTP_201_CREATED, HTTP_204_NO_CONTENT])

        if with_checks:
            withdrawal = response.json()

            # Check that withdrawal exist in db
            try:
                obj = Withdrawal.objects.get(pk=withdrawal['pk'])
            except Withdrawal.DoesNotExist:
                self.fail("Withdrawal object wasn't found in db")

            # Check that withdrawal belongs to an account
            self.assertEqual(obj.account.pk, account['pk'])

            return withdrawal['pk'], obj
