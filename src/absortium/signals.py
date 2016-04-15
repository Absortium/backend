"""
    In order to avoid cycle import problem we should separate models.py and signals.py
"""

__author__ = 'andrew.shvv@gmail.com'

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver
from rest_framework.exceptions import ValidationError

from absortium import constants, celery
from absortium.celery import app
from absortium.crossbarhttp import get_crossbar_client
from absortium.model.models import Account, Exchange, Offer, Withdrawal
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
    exchange = instance
    offer = Offer.objects.filter(price=exchange.price,
                                 primary_currency=exchange.account.currency,
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
        amount = offer.amount - exchange.amount

        # update() is converted directly to an SQL statement; it doesn't call save() on the model
        # instances, and so the pre_save and post_save signals aren't emitted.
        Offer.objects.filter(pk=offer.pk).update(amount=amount)


@receiver(post_save, sender=Exchange, dispatch_uid="exchange_post_save")
def exchange_post_save(sender, instance, *args, **kwargs):
    """
        Create or change offer object if exchange object is received and saved.
    """
    exchange = instance

    offer = Offer.objects.filter(price=exchange.price,
                                 primary_currency=exchange.account.currency,
                                 secondary_currency=exchange.currency).first()

    if offer is None:
        offer = Offer(price=exchange.price,
                      primary_currency=exchange.account.currency,
                      secondary_currency=exchange.currency,
                      amount=exchange.amount)
        offer.save()
    else:
        amount = offer.amount + exchange.amount

        # update() is converted directly to an SQL statement; it doesn't call save() on the model
        # instances, and so the pre_save and post_save signals aren't emitted.
        Offer.objects.filter(pk=offer.pk).update(amount=amount)







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

    client = get_crossbar_client(url=constants.ROUTER_URL)
    client.publish(topic, **publishment)


# @receiver(pre_save, sender=Withdrawal, dispatch_uid="withdraw_pre_save")
# def withdraw_pre_save(sender, instance, *args, **kwargs):
#     withdraw = instance
#     account = withdraw.account
#
#     if account.amount - withdraw.amount >= 0:
#         amount = account.amount - withdraw.amount
#         # update() is converted directly to an SQL statement; it doesn't call save() on the model
#         # instances, and so the pre_save and post_save signals aren't emitted.
#         Account.objects.filter(pk=account.pk).update(amount=amount)
#     else:
#         raise ValidationError("Withdrawal exceed amount of money on the account")


# @receiver(pre_save, sender=Deposit, dispatch_uid="deposit_pre_save")
# def deposit_pre_save(sender, instance, *args, **kwargs):
#     deposit = instance
#     account = deposit.account
#
#     # update() is converted directly to an SQL statement; it doesn't call save() on the model
#     # instances, and so the pre_save and post_save signals aren't emitted.
#     amount = account.amount + deposit.amount
#     Account.objects.filter(pk=account.pk).update(amount=amount)
#
#     #TODO
#     app.do_deposit.delay(deposit.pk)
