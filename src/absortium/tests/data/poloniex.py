from absortium import constants

__author__ = "andrew.shvv@gmail.com"


def create_poloniex_update(update_type="ask", order_type=None,
                           price="0.001",
                           amount="0.001"):
    if order_type not in ["ask", "bid"]:
        raise Exception("Unknown type {}".format(order_type))

    update = {
        "currency_pair": "BTC_ETH",
        "data": {
            "rate": price,
            "type": order_type,
            "amount": amount
        },
        "type": update_type
    }

    if update_type == constants.POLONIEX_OFFER_REMOVED:
        del update['data']['amount']

    return update


def create_order_book(asks, bids):
    return {
        'asks': asks,
        'bids': bids,
        'isFrozen': '0',
        'seq': 66451300,
    }
