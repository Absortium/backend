"""
    In order to avoid cycle import problem we should separate models.py and signals.py
"""

__author__ = 'andrew.shvv@gmail.com'

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver

from absortium.crossbarhttp import get_crossbar_client
from absortium.model.models import Account, Exchange, Offer, Test
from absortium.serializer.serializers import OfferSerializer
from absortium.wallet.base import get_client
from core.utils.logging import getLogger

logger = getLogger(__name__)


# @receiver(post_save, sender=get_user_model(), dispatch_uid="user_post_save")
# def user_post_save(sender, instance, *args, **kwargs):
#     user = instance
#
#     for currency in [constants.BTC, constants.ETH]:
#         account = Account(currency=currency)
#         account.owner = user
#         account.save()


@receiver(pre_save, sender=Account, dispatch_uid="account_pre_save")
def account_pre_save(sender, instance, *args, **kwargs):
    account = instance
    client = get_client(currency=account.currency)
    account.address = client.create_address()


@receiver(post_delete, sender=Exchange, dispatch_uid="exchange_post_delete")
def exchange_post_delete(sender, instance, *args, **kwargs):
    """
        Delete or change offer object if exchange object is removed.
    """
    with transaction.atomic():
        exchange = instance
        offer = Offer.objects.select_for_update().filter(price=exchange.price,
                                                         primary_currency=exchange.from_account.currency,
                                                         secondary_currency=exchange.currency).first()

        if offer is None:
            # TODO: CHANGE EXCEPTION
            raise Exception('There is no offer with such price {}'.format(exchange.price))

        # TODO: Potential place for the error
        # Example: Due to inaccuracies in the calculation of the float number offer.amount - order.amount
        # could be great than zero but actually there is no orders with such price anymore.
        if offer.amount - exchange.amount < 0:
            raise Exception('offer.amount - order.amount < 0')
        elif offer.amount - exchange.amount == 0:
            offer.delete()
        else:
            offer.amount -= exchange.amount

        offer.save()


@receiver(pre_save, sender=Exchange, dispatch_uid="exchange_pre_save")
def exchange_pre_save(sender, instance, *args, **kwargs):
    """
        Create or change offer object if exchange object is received and saved.
    """
    with transaction.atomic():
        new_exchange = instance

        offer = Offer.objects.select_for_update().filter(price=new_exchange.price,
                                                         primary_currency=new_exchange.from_account.currency,
                                                         secondary_currency=new_exchange.currency).first()

        # if exchange is being updated, then we must remove substract previous amount and add new one
        if new_exchange.id:

            # if exchange is updating than offer should exist
            old_exchange = Exchange.objects.select_for_update().get(pk=instance.id)
            offer.amount -= old_exchange.amount
            offer.amount += new_exchange.amount
        else:
            if offer is None:
                offer = Offer(price=new_exchange.price,
                              primary_currency=new_exchange.from_account.currency,
                              secondary_currency=new_exchange.currency,
                              amount=new_exchange.amount)
            else:
                offer.amount += new_exchange.amount

        offer.save()


@receiver(post_save, sender=Offer, dispatch_uid="offer_post_save")
def offer_post_save(sender, instance, *args, **kwargs):
    """
        Send websocket notification to the router if offer is changed.
    """
    offer = instance
    serializer = OfferSerializer(offer)

    publishment = serializer.data
    topic = "{primary_currency}_{secondary_currency}".format(**publishment)
    del publishment['primary_currency']
    del publishment['secondary_currency']

    client = get_crossbar_client()
    client.publish(topic, **publishment)


@receiver(post_delete, sender=Offer, dispatch_uid="offer_post_delete")
def offer_post_delete(sender, instance, *args, **kwargs):
    """
        Send websocket notification to the router if offer is changed.
    """
    offer = instance
    serializer = OfferSerializer(offer)

    publishment = serializer.data
    topic = "{primary_currency}_{secondary_currency}".format(**publishment)
    del publishment['primary_currency']
    del publishment['secondary_currency']

    publishment['amount'] = 0
    client = get_crossbar_client()
    client.publish(topic, **publishment)


@receiver(post_save, sender=Test, dispatch_uid="test_post_save")
def test_post_save(sender, instance, created, *args, **kwargs):
    if not created:
        logger.debug(args)
        logger.debug(kwargs)
        logger.debug("21312312")
