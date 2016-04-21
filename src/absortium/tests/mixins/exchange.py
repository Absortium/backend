__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK

from absortium.model.models import Exchange
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateExchangeMixin():
    def create_exchange(self, account_pk, amount="0.00001", currency="btc", price="0.001", expected_task_status="SUCCESS", expected_exchange_status="COMPLETED",
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
        self.assertEqual(response.status_code, HTTP_200_OK)

        if with_checks:
            task_status = response.json()['status']
            self.assertIn(expected_task_status, task_status)

            if expected_task_status == "SUCCESS":
                self.assertIn("result", response.json().keys())

                incoming_exchange = response.json()['result']
                logger.debug(incoming_exchange)

                # Get the publishment that we sent to the router
                # TODO: This is not good when one mixin depends of methods of another (RouterMixin)

                exchange_status = incoming_exchange['status']
                self.assertEqual(exchange_status, expected_exchange_status)

                if exchange_status == "PENDING":
                    exchange_pk = incoming_exchange["pk"]

                    # Check that exchange exist in db
                    try:
                        exchange = Exchange.objects.get(pk=exchange_pk)
                    except Exchange.DoesNotExist:
                        self.fail("Exchange object wasn't found in db")

                    # Check that exchange belongs to an account
                    self.assertEqual(exchange.from_account.pk, account_pk)

                    return exchange_pk, exchange

                elif exchange_status == "COMPLETED":
                    # TODO: Add check that exchange has status COMPLETED
                    pass
                elif exchange_status == "REJECTED":
                    # TODO: Add check that exchange object was not created
                    pass
