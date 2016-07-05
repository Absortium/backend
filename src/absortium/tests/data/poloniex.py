from absortium import constants

__author__ = "andrew.shvv@gmail.com"


def create_poloniex_update(order_type, offer_type=None,
                           price="0.001",
                           amount="0.001"):
    if order_type == constants.POLONIEX_OFFER_REMOVED:
        if offer_type is None:
            offer_type = "buy"
        elif offer_type not in ["buy", "sell"]:
            raise Exception("Unknown type {}".format(offer_type))

        update = {
            "currency_pair": "BTC_ETH",
            "data": {
                "rate": price,
                "type": offer_type
            },
            "type": "orderBookRemove"
        }

    elif order_type == constants.POLONIEX_OFFER_MODIFIED:

        if offer_type is None:
            offer_type = "ask"
        elif offer_type not in ["ask", "bid"]:
            raise Exception("Unknown type {}".format(offer_type))

        update = {
            "currency_pair": "BTC_ETH",
            "data": {
                "amount": amount,
                "rate": price,
                "type": offer_type
            },
            "type": "orderBookModify",
        }

    elif order_type == constants.POLONIEX_OFFER_CREATED:
        if offer_type is None:
            offer_type = "buy"
        elif offer_type not in ["buy", "sell"]:
            raise Exception("Unknown type {}".format(offer_type))

        update = {
            "currency_pair": "BTC_ETH",
            "data": {
                "amount": amount,
                "rate": price,
                "type": offer_type,
            },
            "type": "newTrade"
        }
    else:
        raise Exception("Unknown 'order_type'")

    return update


def create_order_book(asks=[], bids=[]):
    return {
        'asks': asks,
        'bids': bids,
        'isFrozen': '0',
        'seq': 66451300,
    }
