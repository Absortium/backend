__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from absortium.model.models import Exchange
from absortium.utils import convert
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateExchangeMixin():
    def create_exchange(self, amount="1", from_currency="btc", to_currency="eth", price="1",
                        status="completed", user=None, with_checks=True, debug=False, extra_data={}):
        data = {
            'to_currency': to_currency,
            'from_currency': from_currency,
            'amount': convert(amount),
            'price': price
        }

        for k, v in extra_data.items():
            data[k] = v

        # Authenticate normal user
        if user:
            self.client.force_authenticate(user)

        # Create exchange
        url = '/api/exchanges/'
        response = self.client.post(url, data=data, format='json')

        if debug:
            logger.debug(response.content)

        self.assertIn(response.status_code, [HTTP_201_CREATED, HTTP_204_NO_CONTENT])

        if with_checks:
            history = response.json()
            exchange = history[-1]
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

    def get_exchanges(self, debug=False):

        # Create exchange
        url = '/api/exchanges/'
        response = self.client.get(url, format='json')

        if debug:
            logger.debug(response.content)

        return response.json()



