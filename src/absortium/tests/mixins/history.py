from absortium import constants

__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_200_OK

from core.utils.logging import getLogger

logger = getLogger(__name__)


class HistoryMixin():
    def get_orders_history(self, order_type=None, pair=constants.PAIR_BTC_ETH, debug=False):
        data = {}
        if order_type is not None:
            data.update(type=order_type)

        if pair is not None:
            data.update(pair=pair)

        response = self.client.get('/api/history/', data=data, format='json')
        if debug:
            logger.debug(response.content)

        self.assertEqual(response.status_code, HTTP_200_OK)
        return response.json()
