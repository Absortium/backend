__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from absortium.tests.base import AbsoritumUnitTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class ExchangeTest(AbsoritumUnitTest):
    def test_permissions(self, *args, **kwargs):
        account_pk, _ = self.create_account(self.user, 'btc')
        exchange_pk, _ = self.create_exchange(self.user)

        # Create hacker user
        User = get_user_model()
        hacker = User(username="hacker")
        hacker.save()

        # Authenticate hacker
        self.client.force_authenticate(hacker)

        # Try to get exchanges from another account
        url = '/api/accounts/{account_pk}/exchanges/'.format(account_pk=account_pk)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to create exchange in another account
        data = {
            'currency': 'btc',
            'amount': '0.0111',
            'price': '111'
        }
        url = '/api/accounts/{account_pk}/exchanges/'.format(account_pk=account_pk)
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to get exchange info from another account
        url = '/api/accounts/{account_pk}/exchanges/{exchange_pk}/'.format(account_pk=account_pk,
                                                                           exchange_pk=exchange_pk)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        # Try to delete exchange from another account
        url = '/api/accounts/{account_pk}/exchanges/{exchange_pk}/'.format(account_pk=account_pk,
                                                                           exchange_pk=exchange_pk)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_malformed(self, *args, **kwargs):
        trash_account_pk = "129381728763"
        trash_exchange_pk = "972368423423"

        # Try to get exchange info from uncreated account
        url = '/api/accounts/{account_pk}/exchanges/{exchange_pk}/'.format(account_pk=trash_account_pk,
                                                                           exchange_pk=trash_exchange_pk)

        # Create an account and try to get uncreated exchange
        account_pk, _ = self.create_account(self.user, 'btc')
        url = '/api/accounts/{account_pk}/exchanges/{exchange_pk}/'.format(account_pk=account_pk,
                                                                           exchange_pk=trash_exchange_pk)

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    # TODO: Create test that checks incorrect primary, secondary currency, price, amount etc
    def test_malformed_amount_price(self):
        pass
