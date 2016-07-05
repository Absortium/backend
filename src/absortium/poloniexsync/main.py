import decimal
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


def order2offer(order):
    pair = order["pair"].split("_")
    first_currency = to_db_repr(pair[0])
    second_currency = to_db_repr(pair[1])

    price = Decimal(order["rate"])
    amount = Decimal(order.get("amount", 0))

    if order["type"] in ["buy", "ask", "asks"]:
        price = round(decimal.Decimal("1.0") / price, constants.DECIMAL_PLACES)
        from_currency = first_currency
        to_currency = second_currency

    elif order["type"] in ["sell", "bid", "bids"]:
        from_currency = second_currency
        to_currency = first_currency
    else:
        raise Exception("Unknown order type")

    return {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "price": price,
        "amount": amount,
        "system": constants.SYSTEM_POLONIEX
    }


class PoloniexApp(Application):
    @staticmethod
    def updates_handler(**trade):
        order = trade.get("data")
        order["pair"] = trade.get("currency_pair")

        offer = order2offer(order)
        safe_offer_update(price=offer["price"],
                          from_currency=offer["from_currency"],
                          to_currency=offer["to_currency"],
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

                offer = order2offer(order)
                safe_offer_update(price=offer["price"],
                                  from_currency=offer["from_currency"],
                                  to_currency=offer["to_currency"],
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
