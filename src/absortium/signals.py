"""
    In order to avoid cycle import problem we should separate models and signals
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver

from absortium import constants
from absortium.celery import tasks
from absortium.crossbarhttp import get_crossbar_client
from absortium.model.models import Exchange, Offer, MarketInfo
from absortium.serializers import MarketInfoSerializer, ExchangeSerializer
from absortium.utils import safe_offer_update
from core.utils.logging import getPrettyLogger

__author__ = 'andrew.shvv@gmail.com'

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

    if new_exchange.status == constants.EXCHANGE_INIT:
        safe_offer_update(price=new_exchange.price,
                          from_currency=new_exchange.from_currency,
                          to_currency=new_exchange.to_currency,
                          update=lambda amount: amount + new_exchange.from_amount)

    elif new_exchange.status == constants.EXCHANGE_COMPLETED:
        safe_offer_update(price=new_exchange.price,
                          from_currency=new_exchange.from_currency,
                          to_currency=new_exchange.to_currency,
                          update=lambda amount: amount - new_exchange.from_amount)

        to_repr = {value: key for key, value in constants.AVAILABLE_CURRENCIES.items()}

        serializer = ExchangeSerializer(new_exchange)
        publishment = serializer.data

        topic = constants.TOPIC_HISTORY.format(from_currency=to_repr[new_exchange.from_currency],
                                               to_currency=to_repr[new_exchange.to_currency])

        client = get_crossbar_client()
        client.publish(topic, **publishment)


# @receiver(post_delete, sender=Offer, dispatch_uid="offer_post_delete")
@receiver(post_save, sender=Offer, dispatch_uid="offer_post_save")
def offer_post_save(sender, instance, *args, **kwargs):
    """
        Send websocket notification to the router if offer is changed.
    """

    offer = instance

    amount = sum((offer.amount for offer in Offer.objects.filter(price=offer.price)))

    to_repr = {value: key for key, value in constants.AVAILABLE_CURRENCIES.items()}
    topic = constants.TOPIC_OFFERS.format(from_currency=to_repr[offer.from_currency],
                                          to_currency=to_repr[offer.to_currency])

    publishment = {
        "amount": str(amount),
        "from_currency": to_repr[offer.from_currency],
        "to_currency": to_repr[offer.to_currency],
        "price": str(offer.price)
    }

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
