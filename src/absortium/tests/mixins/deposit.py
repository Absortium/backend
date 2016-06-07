__author__ = 'andrew.shvv@gmail.com'

from django.conf import settings
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from absortium.utils import random_string
from absortium.model.models import Deposit
from core.utils.logging import getPrettyLogger
from absortium.utils import convert

logger = getPrettyLogger(__name__)


class CreateDepositMixin():
    def make_deposit(self, account, amount="99999", with_checks=True, user=None, debug=False):
        data = {
            'amount': convert(amount),
            'address': account['address'],
            'tx_hash': random_string()
        }

        if user:
            # Authenticate normal user
            # TODO: now it is usual user but then we should change it to notification service user!!
            self.client.force_authenticate(user)

        # Create deposit
        if account['currency'] == 'eth':
            url = '/notifications/{currency}/{token}/'.format(currency=account['currency'],
                                                              token=settings.ETH_NOTIFICATION_TOKEN)

        elif account['currency'] == 'btc':
            url = '/notifications/{currency}/{token}/'.format(currency=account['currency'],
                                                              token=settings.BTC_NOTIFICATION_TOKEN)
        else:
            raise Exception("Unknown currency: {}".format(account['currency']))

        response = self.client.post(url, data=data, format='json')

        if debug:
            logger.info(response.content)

        self.assertIn(response.status_code, [HTTP_201_CREATED, HTTP_204_NO_CONTENT])

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
