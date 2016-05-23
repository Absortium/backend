__author__ = 'andrew.shvv@gmail.com'

from decimal import Decimal
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


def get_currency(data, name):
    currency = data.get(name)
    if currency:
        currency = currency.lower()

        if currency in constants.AVAILABLE_CURRENCIES.keys():
            return constants.AVAILABLE_CURRENCIES[currency]
        else:
            raise ValidationError("Not available currency '{}'".format(currency))
    else:
        raise ValidationError("You should specify '{}' field'".format(name))
