__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED

from absortium.model.models import Exchange
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateExchangeMixin():
    def create_exchange(self, amount="0.00001", from_currency="btc", to_currency="eth", price="0.001",
                        status="COMPLETED", user=None, with_checks=True):
        data = {
            'to_currency': to_currency,
            'from_currency': from_currency,
            'amount': amount,
            'price': price
        }

        # Authenticate normal user
        if user:
            self.client.force_authenticate(user)

        # Create exchange
        url = '/api/exchanges/'.format()
        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, HTTP_201_CREATED)

        if with_checks:
            exchange = response.json()
            self.assertEqual(exchange['status'], status)

            if exchange['status'] == "PENDING":
                # Check that exchange exist in db
                try:
                    obj = Exchange.objects.get(pk=exchange["pk"])
                except Exchange.DoesNotExist:
                    self.fail("Exchange object wasn't found in db")

                # Check that exchange belongs to an user
                self.assertNotEqual(obj.owner, None)

                return exchange["pk"], obj

            elif exchange['status'] == "COMPLETED":
                # TODO: Add check that exchange has status COMPLETED
                pass
