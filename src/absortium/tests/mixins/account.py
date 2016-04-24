__author__ = 'andrew.shvv@gmail.com'

import decimal

from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_409_CONFLICT

from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateAccountMixin():
    def create_account(self, currency, with_checks=True, user=None):
        if user:
            # Authenticate normal user
            self.client.force_authenticate(user)

        data = {
            'currency': currency
        }

        # Create account
        response = self.client.post('/api/accounts/', data=data, format='json')
        if with_checks:
            self.assertIn(response.status_code, [HTTP_201_CREATED, HTTP_409_CONFLICT])

        account_pk = response.json()['pk']

        return account_pk, response

    def get_account(self, currency):
        response = self.client.get('/api/accounts/', format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        accounts = response.json()['results']
        for account in accounts:
            if account['currency'] == currency:
                return account['pk'], account

    def check_account_amount(self, account_pk, amount, user=None):
        if user:
            # Authenticate normal user
            self.client.force_authenticate(user)

        # Create account
        response = self.client.get('/api/accounts/{account_pk}/'.format(account_pk=account_pk), format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        account = response.json()
        self.assertEqual(decimal.Decimal(account['amount']), decimal.Decimal(amount))
