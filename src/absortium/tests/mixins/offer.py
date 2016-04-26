__author__ = 'andrew.shvv@gmail.com'

import decimal

from rest_framework.status import HTTP_200_OK

from core.utils.logging import getLogger

logger = getLogger(__name__)


class CheckOfferMixin():
    def check_offer(self, amount, price, from_currency="btc", to_currency="eth", should_exist=True, debug=False):
        data = {
            'from_currency': from_currency,
            'to_currency': to_currency,
        }

        response = self.client.post('/api/offers/', data=data, format='json')
        if debug:
            logger.debug(response.content)

        self.assertEqual(response.status_code, HTTP_200_OK)

        json = response.json()
        offers = json['results']

        amount = decimal.Decimal(amount)
        price = decimal.Decimal(price)

        offer_amount = None
        is_offer_exist = False
        for offer in offers:

            offer_price = decimal.Decimal(offer['price'])
            if offer_price == price:
                offer_amount = decimal.Decimal(offer['amount'])
                is_offer_exist = True

        if should_exist:
            self.assertTrue(is_offer_exist)
            self.assertEqual(offer_amount, amount)
        else:
            self.assertTrue(not is_offer_exist)
