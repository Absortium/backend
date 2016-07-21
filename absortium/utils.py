import decimal
from decimal import Decimal
from random import choice
from string import printable

from rest_framework.exceptions import ValidationError

from absortium import constants
from core.utils.logging import getPrettyLogger

__author__ = 'andrew.shvv@gmail.com'

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


def get_field(data, name, choices, throw=True):
    value = data.get(name)
    if value:
        value = value.lower()

        if value in choices:
            return value
        else:
            raise ValidationError("Value not in the '{}'".format(choices))
    else:
        if throw:
            raise ValidationError("You should specify 'pair' field'".format())
        else:
            return None


def calculate_total_or_amount(data):
    amount = data.get('amount')
    total = data.get('total')

    if total is not None and amount is not None:
        raise ValidationError("only one of the 'amount' or 'total' fields should be presented")

    elif total is None and amount is None:
        raise ValidationError("one of the 'amount' or 'total' fields should be presented")

    price = data.get('price')
    if price is None:
        raise ValidationError("'price' field should be present")

    try:
        price = round(Decimal(price), constants.DECIMAL_PLACES)
    except decimal.InvalidOperation:
        raise ValidationError("'price' field should be decimal serializable")

    if amount is not None and total is None:
        try:
            amount = round(Decimal(amount), constants.DECIMAL_PLACES)
        except decimal.InvalidOperation:
            raise ValidationError("'amount' field should be decimal serializable")

        data['total'] = str(round(amount * price, constants.DECIMAL_PLACES))

    elif total is not None and amount is None:
        try:
            total = round(Decimal(total), constants.DECIMAL_PLACES)
        except decimal.InvalidOperation:
            raise ValidationError("'total' field should be decimal serializable")

        data['amount'] = str(round(total / price, constants.DECIMAL_PLACES))

    return data
