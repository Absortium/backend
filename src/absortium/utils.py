import decimal
from decimal import Decimal

import math

__author__ = 'andrew.shvv@gmail.com'

from random import choice
from string import printable

from rest_framework.exceptions import ValidationError

from absortium import constants
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


def random_string(length=30):
    return "".join([choice(printable) for _ in range(length)])


def retry(exceptions=(), times=1):
    assert (type(exceptions) == tuple)

    logger.debug(exceptions)

    def wrapper(func):
        def decorator(*args, **kwargs):
            try:
                t = 0
                while times > t:
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:

                        t += 1
            except Exception:
                import traceback
                traceback.print_exc()
                logger.debug("{}\n{}".format(type(e), str(e)))
                raise

        return decorator

    return wrapper


def get_currency(data, name, throw=True):
    currency = data.get(name)
    if currency:
        currency = currency.lower()

        if currency in constants.AVAILABLE_CURRENCIES.keys():
            return constants.AVAILABLE_CURRENCIES[currency]
        else:
            raise ValidationError("Not available currency '{}'".format(currency))
    else:
        if throw:
            raise ValidationError("You should specify '{}' field'".format(name))
        else:
            return None


def eth2wei(value):
    try:
        v = Decimal(value) * constants.WEI_IN_ETH
        if type(value) == str:
            return str(round(v))
        else:
            return round(v)

    except decimal.InvalidOperation:
        return value


def wei2eth(value):
    try:
        v = Decimal(value) / constants.WEI_IN_ETH
        if type(value) == str:
            return str(v)
        else:
            return v
    except decimal.InvalidOperation:
        return value


def convert(value):
    """
    Args:
        value: Count of ethereum, btc whihch we want to convert to inner representation. In case of bitcoin
        it will satoshi in case of eth it will be 10 gwei. The point is we divide every currency BTC,ETH on 10 ** 8, so
        we have 8 digits precision.

    Returns:
        In case of BTC the smallest part of this currency is Satoshi => 1BTC = 10 ** 8 Satoshi
        In case of ETH the smallest part is Wei => 1ETH = 10 ** 18 Wei, but we don't want to have such precision, and
        instead of Wei we store 10Gwei (1ETH = 10 ** 9 Gwey = 10 ** 8 * 10Gwei), so 10Gwei in this case is like Satoshi in
        bitcoin.

    """
    try:
        v = Decimal(value) * constants.VIABLE_UNIT
        if type(value) == str:
            return str(round(v))
        else:
            return round(v)
    except decimal.InvalidOperation:
        return value


def deconvert(value):
    try:
        v = Decimal(value) / constants.VIABLE_UNIT
        if type(value) == str:
            return str(v)
        else:
            return v
    except decimal.InvalidOperation:
        return value
