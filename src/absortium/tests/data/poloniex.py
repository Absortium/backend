from absortium import constants

__author__ = "andrew.shvv@gmail.com"


def create_poloniex_update(update_type, order_type=None,
                           price="0.001",
                           amount="0.001"):
    if update_type == constants.POLONIEX_OFFER_REMOVED:
        if order_type is None:
            order_type = "buy"
        elif order_type not in ["buy", "sell"]:
            raise Exception("Unknown type {}".format(order_type))

        update = {
            "currency_pair": "BTC_ETH",
            "data": {
                "rate": price,
                "type": order_type
            },
            "type": "orderBookRemove"
        }

    elif update_type == constants.POLONIEX_OFFER_MODIFIED:

        if order_type is None:
            order_type = "ask"
        elif order_type not in ["ask", "bid"]:
            raise Exception("Unknown type {}".format(order_type))

        update = {
            "currency_pair": "BTC_ETH",
            "data": {
                "amount": amount,
                "rate": price,
                "type": order_type
            },
            "type": "orderBookModify",
        }

    elif update_type == constants.POLONIEX_OFFER_CREATED:
        if order_type is None:
            order_type = "buy"
        elif order_type not in ["buy", "sell"]:
            raise Exception("Unknown type {}".format(order_type))

        update = {
            "currency_pair": "BTC_ETH",
            "data": {
                "amount": amount,
                "rate": price,
                "type": order_type,
            },
            "type": "newTrade"
        }
    else:
        raise Exception("Unknown 'update_type'")

    return update


def create_order_book(asks=[], bids=[]):
    return {
        'asks': asks,
        'bids': bids,
        'isFrozen': '0',
        'seq': 66451300,
    }
