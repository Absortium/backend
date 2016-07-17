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

        response = self.client.post('/api/orders/', data=data, format='json')

        if debug:
            logger.debug(response.content)

        self.assertIn(response.status_code, [HTTP_201_CREATED, HTTP_204_NO_CONTENT])

        history = response.json()
        order = history[-1]

        if with_checks:
            try:
                obj = Order.objects.get(pk=order["pk"])
            except Order.DoesNotExist:
                self.fail("Order object wasn't found in db")

            self.assertEqual(order['status'], status)
            self.assertEqual(order['system'], system)
            self.assertEqual(obj.owner_id, self.client.handler._force_user.pk)

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

    def update_order(self,
                     pk,
                     amount=None,
                     price=None,
                     user=None,
                     with_checks=True,
                     debug=False,
                     extra_data=None):

        data = {}

        if price:
            data['price'] = price

        if amount:
            data['amount'] = amount

        if extra_data:
            for k, v in extra_data.items():
                data[k] = v

        # Authenticate normal user
        if user:
            self.client.force_authenticate(user)

        # Create order
        url = '/api/orders/{pk}/'.format(pk=pk)
        response = self.client.put(url, data=data, format='json')

        if debug:
            logger.debug(response.content)

        self.assertIn(response.status_code, [HTTP_200_OK, HTTP_204_NO_CONTENT])

        order = response.json()

        if with_checks:

            if price is not None:
                self.assertEqual(decimal.Decimal(order['price']), decimal.Decimal(price))

            if amount is not None:
                self.assertEqual(decimal.Decimal(order['amount']), decimal.Decimal(amount))

        return order

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

    def check_order(self,
                    price=None,
                    amount=None,
                    status=None,
                    total=None,
                    pk=None,
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
            c1 = decimal.Decimal(order['price']) == decimal.Decimal(price) if price is not None else True
            c2 = decimal.Decimal(order['amount']) == decimal.Decimal(amount) if amount is not None else True
            c3 = decimal.Decimal(order['total']) == decimal.Decimal(total) if total is not None else True
            c4 = order['status'] == status if status is not None else True
            c5 = order['type'] == order_type if order_type is not None else True
            c6 = order['pk'] == pk if pk is not None else True

            if c1 and c2 and c3 and c4 and c5 and c6:
                is_exist = True

        self.assertEqual(is_exist, should_exist)
