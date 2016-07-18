from absortium import constants

__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_200_OK

from core.utils.logging import getLogger

logger = getLogger(__name__)


class MarketInfoMixin():
    def get_market_info(self,
                        pair=constants.PAIR_BTC_ETH,
                        counts=None,
                        with_checks=True,
                        debug=False):

        params = {}
        if counts:
            params.update(counts=counts)

        if pair:
            params.update(pair=pair)

        # Get market info
        response = self.client.get('/api/marketinfo/', data=params, format='json')
        if debug:
            logger.debug(response.content)

        if with_checks:
            self.assertIn(response.status_code, [HTTP_200_OK])

        results = response.json()

        if len(results) == 1:
            return results[0]
        else:
            return results
