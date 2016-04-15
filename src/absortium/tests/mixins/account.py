__author__ = 'andrew.shvv@gmail.com'

from mock import patch
from rest_framework.status import HTTP_201_CREATED

from absortium.model.models import Account

path_create_address = 'absortium.wallet.bitcoin.BitcoinClient.create_address'
address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"


class CreateAccountMixin():
    @patch(path_create_address, return_value=address)
    def create_account(self, user, currency, with_checks=True, with_authentication=True, *args, **kwargs):
        if with_authentication:
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

            # # Emulate deposit notification
            # self.deposit_notification(account_pk=account_pk)

            accounts = Account.objects.all()
            self.assertEqual(len(accounts), 1)

            account = accounts[0]
            self.assertEqual(account.owner, user)

            return account_pk, account
