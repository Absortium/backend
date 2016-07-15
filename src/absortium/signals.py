"""
    In order to avoid cycle import problem we should separate models and signals
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch.dispatcher import receiver

from absortium import constants
from absortium.celery import tasks
from absortium.crossbarhttp import get_crossbar_client
from absortium.model.models import Order, Offer, MarketInfo
from absortium.serializers import MarketInfoSerializer, OrderSerializer
from absortium.utils import safe_offer_update
from core.utils.logging import getPrettyLogger

__author__ = 'andrew.shvv@gmail.com'

logger = getPrettyLogger(__name__)


@receiver(post_save, sender=get_user_model(), dispatch_uid="user_post_save")
def user_post_save(sender, instance, *args, **kwargs):
    user = instance

    for currency in constants.AVAILABLE_CURRENCIES:
        context = {
            'data': {
                'currency': currency
            },
            'user_pk': user.pk
        }

        tasks.create_account.delay(**context)


@receiver(post_save, sender=Order, dispatch_uid="order_post_save")
def order_post_save(sender, instance, *args, **kwargs):
    """
        Create or change offer object if order object is received and saved.
    """
    new_order = instance

    if new_order.status == constants.ORDER_INIT:
        safe_offer_update(price=new_order.price,
                          pair=new_order.pair,
                          order_type=new_order.type,
                          update=lambda amount: amount + new_order.amount)

    elif new_order.status in [constants.ORDER_COMPLETED, constants.ORDER_CANCELED]:
        safe_offer_update(price=new_order.price,
                          pair=new_order.pair,
                          order_type=new_order.type,
                          update=lambda amount: amount - new_order.amount)

        serializer = OrderSerializer(new_order)
        publishment = serializer.data

        topic = constants.TOPIC_HISTORY.format(pair=new_order.pair, type=new_order.type)

        client = get_crossbar_client()
        client.publish(topic, **publishment)


@receiver(post_delete, sender=Offer, dispatch_uid="offer_post_delete")
@receiver(post_save, sender=Offer, dispatch_uid="offer_post_save")
def offer_update(sender, instance, *args, **kwargs):
    """
        Send websocket notification to the router if offer is changed.
    """

    offer = instance
    offers = Offer.objects.filter(type=offer.type, price=offer.price)

    amount = sum((offer.amount for offer in offers))
    # total = sum((offer.total for offer in offers))

    topic = constants.TOPIC_OFFERS.format(pair=offer.pair, type=offer.type)

    publishment = {
        "amount": str(amount),
        # "total": str(total),
        "pair": offer.pair,
        "type": offer.type,
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
