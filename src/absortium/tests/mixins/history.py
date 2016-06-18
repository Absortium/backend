__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_200_OK

from core.utils.logging import getLogger

logger = getLogger(__name__)


class HistoryMixin():
    def get_exchanges_history(self, from_currency=None, to_currency=None, debug=False):
        data = {}

        if from_currency is not None:
            data["from_currency"] = from_currency

        if to_currency is not None:
            data["to_currency"] = to_currency

        response = self.client.get('/api/history/', data=data, format='json')
        if debug:
            logger.debug(response.content)

        self.assertEqual(response.status_code, HTTP_200_OK)
        return response.json()
