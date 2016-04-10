__author__ = 'andrew.shvv@gmail.com'

BTC_ETH = 0
BTC_XMR = 1
AVAILABLE_PAIRS = {
    'btc_eth': BTC_ETH,
    'btc_xmr': BTC_XMR,
}

SELL = 0
BUY = 1
AVAILABLE_ORDER_TYPES = {
    'sell': SELL,
    'buy': BUY
}

MAX_DIGITS = 15
DECIMAL_PLACES = 6
AMOUNT_MIN_VALUE = 0.000001
PRICE_MIN_VALUE = 0.000001

ROUTER_URL = "http://docker.router:8080/publish"