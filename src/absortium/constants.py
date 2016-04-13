__author__ = 'andrew.shvv@gmail.com'

from decimal import Decimal

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

BTC = 0
ETH = 1
AVAILABLE_CURRENCIES = {
    'btc': BTC,
    'eth': ETH
}

MAX_DIGITS = 15
DECIMAL_PLACES = 8

OFFER_MAX_DIGITS = MAX_DIGITS + (MAX_DIGITS - DECIMAL_PLACES)

AMOUNT_MIN_VALUE = float(Decimal("1") / (Decimal("10") ** DECIMAL_PLACES))
PRICE_MIN_VALUE = float(Decimal("1") / (Decimal("10") ** DECIMAL_PLACES))

ROUTER_URL = "http://docker.router:8080/publish"
