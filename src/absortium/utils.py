from sqlite3 import IntegrityError

from django.db import transaction

from absortium.model.models import Offer

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


def get_or_create_offer(price, from_currency, to_currency, should_exist=False, system=constants.SYSTEM_OWN):
    try:
        with transaction.atomic():
            offer = Offer.objects.select_for_update().get(price=price,
                                                          from_currency=from_currency,
                                                          to_currency=to_currency,
                                                          system=system)
    except Offer.DoesNotExist:
        if should_exist:
            raise
        else:
            offer = Offer(price=price,
                          from_currency=from_currency,
                          to_currency=to_currency,
                          system=system)

    return offer


def safe_offer_update(price, from_currency, to_currency, update, system=constants.SYSTEM_OWN):
    def do():
        with transaction.atomic():
            offer = get_or_create_offer(price=price,
                                        from_currency=from_currency,
                                        to_currency=to_currency,
                                        system=system)

            offer.amount = update(offer.amount)

            if offer.amount > 0:
                offer.save()
            else:
                if offer.pk:
                    offer.delete()

    try:
        do()

    except IntegrityError:
        """
            Multiple offer with the same price might be created if threads/processes simultaneously trying to create
            not existing offer object with similar price. If this happen, duplication integrity error will be thrown,
            this means that thread/process tried to find offer, didn't find it, and then create new one, but another
            thread/process do the same thing. So if we encounter this exception try to get_or_create_offer() second time.
        """
        do()
