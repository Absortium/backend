import decimal

__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from absortium.model.models import Exchange
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateExchangeMixin():
    def create_exchange(self,
                        from_amount="1",
                        to_amount=None,
                        from_currency="btc",
                        to_currency="eth",
                        price="1",
                        status="completed",
                        user=None,
                        with_checks=True,
                        debug=False,
                        extra_data={}):
        data = {
            'to_currency': to_currency,
            'from_currency': from_currency,
            'price': price
        }

        if to_amount is not None:
            data.update(to_amount=to_amount)
        elif from_amount is not None:
            data.update(from_amount=from_amount)

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

    def check_exchange(self, price, amount, from_currency="btc", to_currency="eth", should_exist=True, debug=False):
        exchanges = self.get_exchanges(from_currency, to_currency)

        if debug:
            logger.debug(exchanges)

        is_exist = False
        for exchange in exchanges:
            if decimal.Decimal(exchange['price']) == decimal.Decimal(price) and decimal.Decimal(
                    exchange['from_amount']) == decimal.Decimal(amount):
                is_exist = True

        self.assertEqual(is_exist, should_exist)

    def get_exchanges(self, from_currency=None, to_currency=None, debug=False):

        data = {}
        if from_currency is not None:
            data["from_currency"] = from_currency

        if to_currency is not None:
            data["to_currency"] = to_currency

        # Create exchange
        url = '/api/exchanges/'
        response = self.client.get(url, data, format='json')

        if debug:
            logger.debug(response.content)

        return response.json()
