__author__ = 'andrew.shvv@gmail.com'

import decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient

from absortium.model.models import Address
from .data import coinbase_notification


class MoneyTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        user = User(username="someusername")
        user.save()

        client = APIClient()
        client.force_authenticate(user=user)
        self.client = client
        self.user = user

    def test_notification(self, *args, **kwargs):
        currency = 'btc'

        # Create address object and link it to the user
        coinbase_address = coinbase_notification['data']['address']
        address = Address(currency=currency, address=coinbase_address)
        address.owner = self.user
        address.save()

        # Create mock notification that money was received
        response = self.client.post('/api/money/{}'.format(currency), data=coinbase_notification, format='json')
        self.assertEqual(response.status_code, 200)

        amount = decimal.Decimal(coinbase_notification['additional_data']['amount'])
        self.assertEqual(address.amount, amount)


    def test_withdraw(self, *args, **kwargs):
        currency = 'btc'

        data = {

        }

        # Create address object and link it to the user
        address = Address(currency=currency, address="34567uhGY6754e367", amount=decimal.Decimal("1.00"))
        address.owner = self.user
        address.save()

        # Create mock notification that money was received
        response = self.client.delete('/api/money/{}'.format(currency), data=data, format='json')
        self.assertEqual(response.status_code, 200)

        amount = decimal.Decimal(coinbase_notification['additional_data']['amount'])
        self.assertEqual(address.amount, amount)
