import decimal

from absortium import constants

__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_200_OK

from absortium.model.models import Order
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CreateOrderMixin():
    def create_order(self,
                     amount="1",
                     price="1",
                     total=None,
                     order_type=constants.ORDER_BUY,
                     pair=constants.PAIR_BTC_ETH,
                     status=constants.ORDER_COMPLETED,
                     system=constants.SYSTEM_OWN,
                     need_approve=False,
                     user=None,
                     with_checks=True,
                     debug=False,
                     extra_data={}):
        data = {
            'type': order_type,
            'price': price,
            'pair': pair,
            'need_approve': need_approve
        }

        if total is not None:
            data.update(total=total)
        elif amount is not None:
            data.update(amount=amount)

        for k, v in extra_data.items():
            data[k] = v

        # Authenticate normal user
        if user:
            self.client.force_authenticate(user)

        # Create order
        url = '/api/orders/'
        response = self.client.post(url, data=data, format='json')

        if debug:
            logger.debug(response.content)

        self.assertIn(response.status_code, [HTTP_201_CREATED, HTTP_204_NO_CONTENT])

        history = response.json()
        order = history[-1]

        if with_checks:
            self.assertEqual(order['status'], status)
            self.assertEqual(order['system'], system)

            if order['status'] == "PENDING":
                # Check that order exist in db
                try:
                    obj = Order.objects.get(pk=order["pk"])
                except Order.DoesNotExist:
                    self.fail("Order object wasn't found in db")

                # Check that order belongs to an user
                self.assertNotEqual(obj.owner, None)

            elif order['status'] == "COMPLETED":
                # TODO: Add check that order has status COMPLETED
                pass

        return order

    def cancel_order(self,
                     pk,
                     user=None,
                     debug=False):

        # Authenticate normal user
        if user:
            self.client.force_authenticate(user)

        # Create order
        url = '/api/orders/{pk}/'.format(pk=pk)
        response = self.client.delete(url, format='json')

        if debug:
            logger.debug(response.content)

        self.assertIn(response.status_code, [HTTP_200_OK, HTTP_204_NO_CONTENT])

    def approve_order(self,
                      pk,
                      user=None,
                      debug=False):

        # Authenticate normal user
        if user:
            self.client.force_authenticate(user)

        # Create order
        url = '/api/orders/{pk}/approve/'.format(pk=pk)
        response = self.client.post(url, format='json')

        if debug:
            logger.debug(response.content)

        self.assertIn(response.status_code, [HTTP_200_OK])

    def check_order(self,
                    price,
                    amount,
                    status,
                    order_type=constants.ORDER_BUY,
                    pair=constants.PAIR_BTC_ETH,
                    should_exist=True,
                    debug=False):
        orders = self.get_orders(order_type=order_type,
                                 pair=pair)

        if debug:
            logger.debug(orders)

        is_exist = False
        for order in orders:
            c1 = decimal.Decimal(order['price']) == decimal.Decimal(price)
            c2 = decimal.Decimal(order['amount']) == decimal.Decimal(amount)
            c3 = order['status'] == status
            c4 = order['type'] == order_type

            if c1 and c2 and c3 and c4:
                is_exist = True

        self.assertEqual(is_exist, should_exist)

    def get_orders(self,
                   order_type=constants.ORDER_BUY,
                   pair=constants.PAIR_BTC_ETH,
                   debug=False):

        data = {
            "pair": pair,
            "type": order_type
        }

        # Create order
        url = '/api/orders/'
        response = self.client.get(url, data, format='json')

        if debug:
            logger.debug(response.content)

        return response.json()
