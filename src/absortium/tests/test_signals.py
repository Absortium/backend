__author__ = 'andrew.shvv@gmail.com'

import decimal
import random

from core.utils.logging import getLogger
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient

from absortium.constants import BTC_ETH, SELL, MAX_DIGITS, DECIMAL_PLACES, AMOUNT_MIN_VALUE
from absortium.model.models import Offer, Order

logger = getLogger(__name__)


def random_amount():
    amount = -1
    while amount < AMOUNT_MIN_VALUE:
        amount = decimal.Decimal('%d.%d' % (random.randint(0, MAX_DIGITS), random.randint(0, DECIMAL_PLACES)))
    return amount


class SignalTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        user = User(username="someusername")
        user.save()

        client = APIClient()
        client.force_authenticate(user=user)
        self.client = client
        self.user = user

    def test_order_post_save(self, *args, **kwargs):
        n = 3

        for i in range(0, n):
            order = Order(type=SELL, amount=1, price=1, pair=BTC_ETH, owner=self.user)
            order.save()

        offers = Offer.objects.filter(type=SELL, price=1, pair=BTC_ETH).all()

        # Count of offers should be equal to 1 because price is similar for all created orders
        self.assertEqual(len(offers), 1)

        offer = offers[0]

        # Amount of offers should be equal to 3 because price is similar for all created orders
        # and all orders should be merged in one offer
        self.assertEqual(offer.amount, n)

    def test_order_post_save_inaccuracies(self, *args, **kwargs):
        price = 1
        order_type = 'sell'
        currency_pair = 'btc_eth'
        order_data = {
            'type': order_type,
            'price': price,
            'pair': currency_pair,
        }

        amounts = [random_amount() for _ in range(10)]
        for amount in amounts:
            order_data['amount'] = amount
            response = self.client.post('/api/orders/', data=order_data, format='json')
            self.assertEqual(response.status_code, 201)

        response = self.client.get('/api/offers/{}/{}'.format(currency_pair, order_type), format='json')
        self.assertEqual(response.status_code,  200)

        offers = Offer.objects.filter(type=SELL, price=price, pair=BTC_ETH).all()

        # Count of offers should be equal to 1 because price is similar for all created orders
        self.assertEqual(len(offers), 1)

        offer = offers[0]

        # Shouldn't be inaccurancies
        self.assertEqual(offer.amount, sum(amounts))
