__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED

from absortium.model.models import Exchange
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateExchangeMixin():
    def create_exchange(self, account_pk, amount="0.00001", currency="btc", price="0.001", status="COMPLETED",
                        user=None, with_checks=True):
        data = {
            'currency': currency,
            'amount': amount,
            'price': price
        }

        # Authenticate normal user
        if user:
            self.client.force_authenticate(user)

        # Create exchange
        url = '/api/accounts/{account_pk}/exchanges/'.format(account_pk=account_pk)
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)

        if with_checks:
            task_id = response.json()['task_id']

            # Get the publishment that we sent to the router
            # TODO: This is not good when one mixin depends of methods of another (RouterMixin)
            publishment = self.get_publishment_by_task_id(task_id=task_id)
            self.assertNotEqual(publishment, None)

            incoming_status = publishment["data"]['status']
            self.assertEqual(incoming_status, status)

            if incoming_status == "PENDING" or incoming_status == "INIT":
                exchange_pk = publishment["data"]["pk"]

                # Check that exchange exist in db
                try:
                    exchange = Exchange.objects.get(pk=exchange_pk)
                except Exchange.DoesNotExist:
                    self.fail("Exchange object wasn't found in db")

                # Check that exchange belongs to an account
                self.assertEqual(exchange.from_account.pk, account_pk)

                return exchange_pk, exchange

            elif incoming_status == "COMPLETED":
                # TODO: Add check that exchange has status COMPLETED
                pass
            elif incoming_status == "REJECTED":
                # TODO: Add check that exchange object was not created
                pass
