from decimal import Decimal

from absortium import constants
from absortium.utils import safe_offer_update
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)

__author__ = "andrew.shvv@gmail.com"

from poloniex.app import Application


class PoloniexApp(Application):
    @staticmethod
    def update_offers(**update):
        order = update.get('data')
        pair = update.get('currency_pair').split("_")

        price = Decimal(order["rate"])
        amount = Decimal(order.get("amount", 0))

        to_db_repr = lambda key: constants.AVAILABLE_CURRENCIES[key.lower()]

        if order["type"] in ["buy", "ask"]:
            from_currency = to_db_repr(pair[0])
            to_currency = to_db_repr(pair[1])

        elif order["type"] in ["sell", "bid"]:
            from_currency = to_db_repr(pair[1])
            to_currency = to_db_repr(pair[0])
        else:
            raise Exception("Unknown order type")

        def update_amount(*args, **kwargs):
            if update.get("type") in [constants.POLONIEX_OFFER_CREATED, constants.POLONIEX_OFFER_MODIFIED]:
                return amount
            elif update.get("type") == constants.POLONIEX_OFFER_REMOVED:
                return 0
            else:
                raise Exception("Unknown update type")

        safe_offer_update(price=price,
                          from_currency=from_currency,
                          to_currency=to_currency,
                          system=constants.SYSTEM_POLONIEX,
                          update=update_amount)

    async def main(self):
        self.push_api.subscribe(topic="BTC_ETH", handler=PoloniexApp.update_offers)
