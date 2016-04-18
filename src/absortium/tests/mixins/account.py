__author__ = 'andrew.shvv@gmail.com'

import decimal

from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK

from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateAccountMixin():
    def create_account(self, currency, with_checks=False, user=None):
        if user:
            # Authenticate normal user
            self.client.force_authenticate(user)

        data = {
            'currency': currency
        }

        # Create account
        response = self.client.post('/api/accounts/', data=data, format='json')
        if with_checks:
            self.assertEqual(response.status_code, HTTP_201_CREATED)

        account_pk = response.json()['pk']

        return account_pk, response

    def check_account_amount(self, account_pk, amount, user=None):
        if user:
            # Authenticate normal user
            self.client.force_authenticate(user)

        # Create account
        response = self.client.get('/api/accounts/{account_pk}/'.format(account_pk=account_pk), format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        account = response.json()
        self.assertEqual(decimal.Decimal(account['amount']), decimal.Decimal(amount))
