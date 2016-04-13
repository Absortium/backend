__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED

from absortium.model.models import Exchange
from core.utils.logging import getLogger

logger = getLogger(__name__)


class ExchangeMixin():
    def create_exchange(self, user, amount="0.00001", currency="btc", price="0.001"):
        data = {
            'currency': currency,
            'amount': amount,
            'price': price
        }

        # Authenticate normal user
        self.client.force_authenticate(user)

        # Get list of accounts
        response = self.client.get('/api/accounts/', format='json')
        account = self.get_first(response)
        account_pk = account['pk']

        # Create account
        url = '/api/accounts/{account_pk}/exchanges/'.format(account_pk=account_pk)
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        exchange_pk = response.json()['pk']

        # Check that exchange exist in db
        exchanges = Exchange.objects.all()
        self.assertEqual(len(exchanges), 1)

        # Check that exchange belongs to an account
        exchange = exchanges[0]
        self.assertEqual(exchange.account.pk, account_pk)

        return exchange_pk, exchange
