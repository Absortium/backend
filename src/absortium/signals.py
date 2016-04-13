"""
    In order to avoid cycle import problem we should separate models.py and signals.py
"""

__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver

from absortium import constants
from absortium.crossbarhttp import get_crossbar_client
from absortium.model.models import Order, Offer, Account
from absortium.serializer.serializers import OfferSerializer
from absortium.wallet.base import get_client


# @receiver(post_save, sender=get_user_model(), dispatch_uid="user_post_save")
# def user_post_save(sender, instance, *args, **kwargs):
#     user = instance
#
#     for currency in [constants.BTC, constants.ETH]:
#         account = Account(currency=currency)
#         account.owner = user
#         account.save()


@receiver(pre_save, sender=Account, dispatch_uid="account_post_save")
def account_post_save(sender, instance, *args, **kwargs):
    account = instance
    client = get_client(currency=account.currency)
    account.address = client.create_address()


@receiver(post_delete, sender=Order, dispatch_uid="order_post_delete")
def order_post_delete(sender, instance, *args, **kwargs):
    order = instance
    offer = Offer.objects.filter(price=order.price, pair=order.pair, type=order.type)

    if offer is None:
        # TODO: CHANGE EXCEPTION
        raise Exception('There is no offer with such price {}'.format(order.price))

    # TODO: Potential place for the error
    # Example: Due to inaccuracies in the calculation of the float number offer.amount - order.amount
    # could be great than zero but actually there is no orders with such price anymore.
    if offer.amount - order.amount < 0:
        raise Exception('offer.amount - order.amount < 0')
    elif offer.amount - order.amount == 0:
        offer.delete()
    else:
        offer.amount -= order.amount
        offer.save()


@receiver(post_delete, sender=Order, dispatch_uid="order_post_delete")
def order_post_delete(sender, instance, *args, **kwargs):
    order = instance
    offer = Offer.objects.filter(price=order.price, pair=order.pair, type=order.type)

    if offer is None:
        # TODO: CHANGE EXCEPTION
        raise Exception('There is no offer with such price {}'.format(order.price))

    # TODO: Potential place for the error
    # Example: Due to inaccuracies in the calculation of the float number offer.amount - order.amount
    # could be great than zero but actually there is no orders with such price anymore.
    if offer.amount - order.amount < 0:
        raise Exception('offer.amount - order.amount < 0')
    elif offer.amount - order.amount == 0:
        offer.delete()
    else:
        offer.amount -= order.amount
        offer.save()


@receiver(post_save, sender=Order, dispatch_uid="order_post_save")
def order_post_save(sender, instance, *args, **kwargs):
    order = instance
    offer = Offer.objects.filter(price=order.price, pair=order.pair, type=order.type).first()

    if offer is None:
        offer = Offer(price=order.price,
                      pair=order.pair,
                      type=order.type,
                      amount=order.amount)
    else:
        offer.amount += order.amount

    offer.save()


@receiver(post_save, sender=Offer, dispatch_uid="offer_post_save")
def offer_post_save(sender, instance, *args, **kwargs):
    offer = instance
    serializer = OfferSerializer(offer)

    publishment = serializer.data
    topic = publishment['pair']
    del publishment['pair']

    client = get_crossbar_client(url=constants.ROUTER_URL)
    client.publish(topic, **publishment)
