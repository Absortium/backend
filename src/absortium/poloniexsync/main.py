from decimal import Decimal

from absortium import constants
from absortium.model.models import Offer
from absortium.utils import safe_offer_update
from core.utils.logging import getPrettyLogger
from poloniex.app import Application

__author__ = "andrew.shvv@gmail.com"

logger = getPrettyLogger(__name__)

CURRENCY_PAIR = "BTC_ETH"
to_db_repr = lambda key: constants.AVAILABLE_CURRENCIES[key.lower()]


def update2offer(order):
    price = Decimal(order["rate"])
    amount = Decimal(order.get("amount", 0))

    if order["type"] in ["bid", "bids"]:
        offer_type = constants.ORDER_BUY
    elif order["type"] in ["ask", "asks"]:
        offer_type = constants.ORDER_SELL
    else:
        raise Exception("Unknown order type")

    return {
        "pair": order["pair"].lower(),
        "type": offer_type,
        "price": price,
        "amount": amount,
        "system": constants.SYSTEM_POLONIEX
    }


class PoloniexApp(Application):
    @staticmethod
    def updates_handler(**update):
        if update.get('type') in [constants.POLONIEX_OFFER_REMOVED, constants.POLONIEX_OFFER_MODIFIED]:
            order = update.get("data")
            order["pair"] = update.get("currency_pair")

            offer = update2offer(order)
            safe_offer_update(price=offer["price"],
                              pair=offer["pair"],
                              order_type=offer["type"],
                              system=offer["system"],
                              update=lambda *args: offer["amount"])

    @staticmethod
    def synchronize_offers(orders):
        def sync(orders, _type):
            for price, amount in orders[_type]:
                order = {
                    "rate": price,
                    "amount": amount,
                    "pair": CURRENCY_PAIR,
                    "type": _type
                }

                offer = update2offer(order)
                safe_offer_update(price=offer["price"],
                                  pair=offer["pair"],
                                  order_type=offer["type"],
                                  system=offer["system"],
                                  update=lambda *args: offer["amount"])

        sync(orders, "bids")
        sync(orders, "asks")

    async def main(self):
        Offer.objects.filter(system=constants.SYSTEM_POLONIEX).delete()

        # Subscribe on order update to keep offers synchronized with Poloniex.
        self.push_api.subscribe(topic=CURRENCY_PAIR, handler=PoloniexApp.updates_handler)

        # Download all Poloniex orders; convert them to offers; add them to the system.
        orders = await self.public_api.returnOrderBook(CURRENCY_PAIR)
        PoloniexApp.synchronize_offers(orders)
