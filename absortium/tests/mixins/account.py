from decimal import Decimal as D

from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_409_CONFLICT

from absortium.model.models import Account
from core.utils.logging import getLogger

__author__ = 'andrew.shvv@gmail.com'

logger = getLogger(__name__)

ACCOUNT_URL = "/api/accounts/"


class CreateAccountMixin():
    def create_account(self, currency, with_checks=True, user=None, extra_data=None):
        if user:
            # Authenticate normal user
            self.client.force_authenticate(user)

        data = {'currency': currency}

        if extra_data:
            for k, v in extra_data.items():
                data[k] = v

        response = self.client.post(ACCOUNT_URL, data=data, format='json')
        self.assertIn(response.status_code, [HTTP_201_CREATED, HTTP_409_CONFLICT])

        account = response.json()

        if with_checks:
            try:
                obj = Account.objects.get(pk=account["pk"])
            except Account.DoesNotExist:
                self.fail("Account object wasn't found in db")

            self.assertEqual(obj.owner_id, self.client.handler._force_user.pk)
            self.assertEqual(D(account['amount']), D('0.0'))
            self.assertEqual(account['currency'], currency)

        return response.json()

    def get_account(self, currency, user=None, debug=False):
        if user:
            self.client.force_authenticate(user)

        response = self.client.get('{url}{currency}/'.format(url=ACCOUNT_URL, currency=currency), format='json')

        if debug:
            logger.debug(response.content)

        self.assertEqual(response.status_code, HTTP_200_OK)
        return response.json()

    def delete_account(self, currency, debug=False):
        response = self.client.delete('{url}{currency}/'.format(url=ACCOUNT_URL, currency=currency), format='json')

        if debug:
            logger.debug(response.content)

        self.assertEqual(response.status_code, HTTP_200_OK)
        return response

    def check_account_amount(self, account, amount, user=None, debug=False):
        if user:
            # Authenticate normal user
            self.client.force_authenticate(user)

        if type(amount) == str:
            amount = D(amount)

        account = self.get_account(account['currency'])
        self.assertEqual(D(account['amount']), amount)
