from random import choice
from sqlite3 import IntegrityError
from string import printable

from django.db import transaction
from rest_framework.exceptions import ValidationError

from absortium import constants
from absortium.model.models import Offer
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


def get_or_create_offer(price, order_type, pair, should_exist=False, system=constants.SYSTEM_OWN):
    try:
        with transaction.atomic():
            offer = Offer.objects.select_for_update().get(price=price,
                                                          pair=pair,
                                                          type=order_type,
                                                          system=system)
    except Offer.DoesNotExist:
        if should_exist:
            raise
        else:
            offer = Offer(price=price,
                          pair=pair,
                          type=order_type,
                          system=system)

    return offer


def safe_offer_update(price, order_type, pair, update, system=constants.SYSTEM_OWN):
    def do():
        with transaction.atomic():
            offer = get_or_create_offer(price=price,
                                        pair=pair,
                                        order_type=order_type,
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
            thread/process do the same thing. So if we encounter this exception try to do() second time.
        """
        do()
