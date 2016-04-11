__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from mock import patch
from rest_framework.test import APITestCase, APIClient

from absortium import constants
from absortium.models import Address
from .data import coinbase_response


class AddressTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        user = User(username="someusername")
        user.save()

        client = APIClient()
        client.force_authenticate(user=user)
        self.client = client
        self.user = user

    def test_creation(self, *args, **kwargs):
        currency = 'btc'

        with patch('absortium.wallet.bitcoin.create_address', return_value=coinbase_response):
            response = self.client.post('/api/address/{}'.format(currency), format='json')
            self.assertEqual(response.status_code, 201)

            addresses = Address.objects.all()
            self.assertEqual(len(addresses), 1)

            address = addresses[0]

            self.assertEqual(address.address, coinbase_response['data']['address'])
            self.assertEqual(address.currency, constants.BTC)
            self.assertEqual(address.owner, self.user)
