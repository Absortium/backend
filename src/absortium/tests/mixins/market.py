__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_200_OK

from core.utils.logging import getLogger

logger = getLogger(__name__)


class MarketInfoMixin():
    def get_market_info(self, from_currency="btc", to_currency="eth", counts="1", with_checks=True, debug=False):
        params = {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'counts': counts,
        }

        # Get market info
        response = self.client.get('/api/marketinfo/', data=params, format='json')
        if debug:
            logger.debug(response.content)

        if with_checks:
            self.assertIn(response.status_code, [HTTP_200_OK])

        results = response.json()

        if int(counts) == 1:
            return results[0]
        else:
            return results
