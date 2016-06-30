"""
    In order to avoid cycle import problem we should separate models and signals
"""

__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.db.utils import IntegrityError
from django.dispatch.dispatcher import receiver

from absortium import constants
from absortium.celery import tasks
from absortium.crossbarhttp import get_crossbar_client
from absortium.model.models import Exchange, Offer, MarketInfo
from absortium.serializers import OfferSerializer, MarketInfoSerializer, ExchangeSerializer
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


@receiver(post_save, sender=get_user_model(), dispatch_uid="user_post_save")
def user_post_save(sender, instance, *args, **kwargs):
    user = instance

    for currency in constants.AVAILABLE_CURRENCIES.keys():
        context = {
            'data': {
                'currency': currency
            },
            'user_pk': user.pk
        }

        tasks.create_account.delay(**context)


@receiver(post_save, sender=Exchange, dispatch_uid="exchange_post_save")
def exchange_post_save(sender, instance, *args, **kwargs):
    """
        Create or change offer object if exchange object is received and saved.
    """
    new_exchange = instance

    def get_or_create_offer(should_exist=False):
        try:
            with transaction.atomic():
                offer = Offer.objects.select_for_update().get(price=new_exchange.price,
                                                              from_currency=new_exchange.from_currency,
                                                              to_currency=new_exchange.to_currency)
        except Offer.DoesNotExist:
            if should_exist:
                raise
            else:
                offer = Offer(price=new_exchange.price,
                              from_currency=new_exchange.from_currency,
                              to_currency=new_exchange.to_currency)

        return offer

    if new_exchange.status == constants.EXCHANGE_INIT:
        try:
            with transaction.atomic():
                offer = get_or_create_offer()
                offer.amount += new_exchange.amount
                offer.save()

        except IntegrityError:
            """
                Multiple offer with the same price might be created if celery tasks simultaneously trying to create
                not existing offer object with similar price. If this happen, duplication integrity error will be thrown,
                this means that celery task tried to find offer, didn't find it, and then create new one, but another celery
                task do the same thing. So if we encounter this exception try to get_or_create_offer() second time.
            """
            with transaction.atomic():
                offer = get_or_create_offer()
                offer.amount += new_exchange.amount
                offer.save()

    elif new_exchange.status == constants.EXCHANGE_COMPLETED:
        with transaction.atomic():
            offer = get_or_create_offer(should_exist=True)

            # TODO: Potential place for the error
            # Example: Due to inaccuracies in the calculation of the float number offer.amount - order.amount
            # could be great than zero but actually there is no orders with such price anymore.
            if offer.amount - new_exchange.amount < 0:
                # TODO: Inaccuracy warning!
                offer.delete()
            elif offer.amount - new_exchange.amount == 0:
                offer.delete()
            else:
                offer.amount -= new_exchange.amount
                offer.save()

            to_repr = {value: key for key, value in constants.AVAILABLE_CURRENCIES.items()}

            serializer = ExchangeSerializer(new_exchange)
            publishment = serializer.data

            topic = constants.TOPIC_HISTORY.format(from_currency=to_repr[new_exchange.from_currency],
                                                   to_currency=to_repr[new_exchange.to_currency])

            client = get_crossbar_client()
            client.publish(topic, **publishment)


@receiver(post_save, sender=Offer, dispatch_uid="offer_post_save")
def offer_post_save(sender, instance, *args, **kwargs):
    """
        Send websocket notification to the router if offer is changed.
    """
    offer = instance
    serializer = OfferSerializer(offer)

    publishment = serializer.data
    to_repr = {value: key for key, value in constants.AVAILABLE_CURRENCIES.items()}
    topic = constants.TOPIC_OFFERS.format(from_currency=to_repr[offer.from_currency],
                                          to_currency=to_repr[offer.to_currency])

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
    to_repr = {value: key for key, value in constants.AVAILABLE_CURRENCIES.items()}

    topic = constants.TOPIC_OFFERS.format(from_currency=to_repr[offer.from_currency],
                                          to_currency=to_repr[offer.to_currency])

    publishment['amount'] = 0
    client = get_crossbar_client()
    client.publish(topic, **publishment)


@receiver(post_save, sender=MarketInfo, dispatch_uid="market_info_post_save")
def market_info_post_save(sender, instance, *args, **kwargs):
    """
        Send websocket notification to the router if offer is changed.
    """
    info = instance
    serializer = MarketInfoSerializer(info)
    publishment = serializer.data

    client = get_crossbar_client()
    client.publish(constants.TOPIC_MARKET_INFO, **publishment)
