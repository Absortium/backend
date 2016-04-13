__author__ = 'andrew.shvv@gmail.com'

from mock import patch
from rest_framework.status import HTTP_201_CREATED

from absortium.model.models import Account

path_create_address = 'absortium.wallet.bitcoin.BitcoinClient.create_address'
address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"


class AccountMixin():
    @patch(path_create_address, return_value=address)
    def create_account(self, user, currency, *args, **kwargs):
        data = {
            'currency': currency
        }

        # Authenticate normal user
        self.client.force_authenticate(user)

        # Create account

        response = self.client.post('/api/accounts/', data=data, format='json')

        self.assertEqual(response.status_code, HTTP_201_CREATED)
        account_pk = response.json()['pk']

        accounts = Account.objects.all()
        self.assertEqual(len(accounts), 1)

        account = accounts[0]
        self.assertEqual(account.owner, user)

        return account_pk, account
