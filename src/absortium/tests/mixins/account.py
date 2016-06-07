from decimal import Decimal

__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_409_CONFLICT
from absortium.utils import convert, eth2wei
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
        accounts = self.get_accounts()
        for account in accounts:
            if account['currency'] == currency:
                account['amount'] = Decimal(account['amount'])
                return account

    def get_accounts(self):
        response = self.client.get('/api/accounts/', format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        return response.json()

    def check_account_amount(self, account, amount, user=None):
        if user:
            # Authenticate normal user
            self.client.force_authenticate(user)

        # Create account
        response = self.client.get('/api/accounts/{account_pk}/'.format(account_pk=account['pk']), format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        account = response.json()

        self.assertEqual(Decimal(account['amount']), Decimal(convert(amount)))
