__author__ = 'andrew.shvv@gmail.com'
from django.test import override_settings
from rest_framework.status import HTTP_201_CREATED

from absortium.model.models import Withdrawal
from absortium.tests.lockmanager.mixins import LockManagerMixin
from absortium.tests.router.mixins import RouterMixin
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateWithdrawalMixin(RouterMixin, LockManagerMixin):
    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True)
    def create_withdrawal(self, user, amount="0.00001"):
        data = {
            'amount': amount,
            'address': '1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX'
        }

        # Authenticate normal user
        # TODO: now it is usual user but then we should change it to notification service user!!
        self.client.force_authenticate(user)

        # Get list of accounts
        # TODO: now get account lists but then notification server will search account by address given in notification from coinbase!!
        response = self.client.get('/api/accounts/', format='json')
        account = self.get_first(response)
        account_pk = account['pk']

        # Create withdrawal
        url = '/api/accounts/{account_pk}/withdrawals/'.format(account_pk=account_pk)
        response = self.client.post(url, data=data, format='json')
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
