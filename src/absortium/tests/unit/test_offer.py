__author__ = 'andrew.shvv@gmail.com'

import decimal
import random

from rest_framework.status import HTTP_200_OK

from absortium import constants
from absortium.tests.base import AbsoritumUnitTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class OfferTest(AbsoritumUnitTest):
    before_dot = 10 ** (constants.MAX_DIGITS - constants.DECIMAL_PLACES) - 1
    after_dot = 10 ** constants.DECIMAL_PLACES - 1

    def random_amount(self):
        amount = -1

        while amount < constants.AMOUNT_MIN_VALUE:
            amount = decimal.Decimal('%d.%d' % (random.randint(0, self.before_dot), random.randint(0, self.after_dot)))
        return amount

    def test_calculation_accuracy(self, *args, **kwargs):
        account_pk, _ = self.create_account('btc')
        self.create_account("eth")

        n = 20
        amounts = [self.random_amount() for _ in range(0, n)]

        for amount in amounts:
            self.create_deposit(account_pk, amount=amount)
            self.create_exchange(account_pk, currency="eth", amount=str(amount), price="0.1", expected_exchange_status="INIT")

        data = {
            'primary_currency': 'btc',
            'secondary_currency': 'eth',
        }

        response = self.client.post('/api/offers/', data=data, format='json')
        offer = self.get_first(response)

        self.assertEqual(decimal.Decimal(offer['amount']), sum(amounts))

    def test_different_price(self, *args, **kwargs):
        account_pk, _ = self.create_account('btc')
        self.create_account("eth")
        self.create_deposit(account_pk, amount="999999.0")

        self.create_exchange(account_pk, currency="eth", amount="1.0", price="1", expected_exchange_status="INIT")
        self.create_exchange(account_pk, currency="eth", amount="1.0", price="2", expected_exchange_status="INIT")

        data = {
            'primary_currency': 'btc',
            'secondary_currency': 'eth',
        }

        response = self.client.post('/api/offers/', data=data, format='json')
        self.assertEqual(response.status_code, HTTP_200_OK)

        json = response.json()
        results = json['results']

        self.assertEqual(len(results), 2)

    # TODO: Create test that checks incorrect primary, secondary currency
    def test_malformed(self):
        pass
