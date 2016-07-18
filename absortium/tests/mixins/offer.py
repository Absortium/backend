from decimal import Decimal

from absortium import constants

__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_200_OK
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CheckOfferMixin():
    def check_offer(self,
                    amount="1",
                    price="1",
                    pair=constants.PAIR_BTC_ETH,
                    order_type=constants.ORDER_BUY,
                    should_exist=True, debug=False):
        data = {
            'pair': pair,
            'type': order_type,
        }

        response = self.client.get('/api/offers/', data=data, format='json')
        if debug:
            logger.debug(response.content)

        self.assertEqual(response.status_code, HTTP_200_OK)

        offers = response.json()

        amount = Decimal(amount)
        price = Decimal(price)

        offer_amount = None
        offer_type = None
        is_offer_exist = False

        for offer in offers:
            offer_price = Decimal(offer['price'])
            if offer_price == price:
                offer_amount = Decimal(offer['amount'])
                offer_type = offer['type']
                is_offer_exist = True

        if should_exist:
            self.assertTrue(is_offer_exist)
            self.assertEqual(offer_amount, round(amount, constants.DECIMAL_PLACES))
            self.assertEqual(offer_type, order_type)
        else:
            self.assertTrue(not is_offer_exist)

    def check_offers_empty(self, debug=False):

        response = self.client.get('/api/offers/', format='json')
        if debug:
            logger.debug(response.content)

        self.assertEqual(response.status_code, HTTP_200_OK)
        offers = response.json()

        self.assertEqual(len(offers), 0)

    def get_offers(self, debug=False):
        response = self.client.get('/api/offers/', format='json')
        if debug:
            logger.debug(response.content)

        self.assertEqual(response.status_code, HTTP_200_OK)
        return response.json()
