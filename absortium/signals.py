"""
    In order to avoid cycle import problem we should separate models and signals
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from absortium import constants
from absortium.celery import tasks
from absortium.crossbarhttp import get_crossbar_client
from absortium.model.models import Order, MarketInfo
from absortium.serializers import MarketInfoSerializer, OrderSerializer
from core.apikeyauth.models import Client
from core.utils.logging import getPrettyLogger

__author__ = 'andrew.shvv@gmail.com'

logger = getPrettyLogger(__name__)


@receiver(post_save, sender=get_user_model(), dispatch_uid="user_post_save")
def user_post_save(sender, instance, *args, **kwargs):
    user = instance

    c = Client(owner_id=user.pk)
    c.save()

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

    def history_notification(order):
        if order.status in [constants.ORDER_COMPLETED, constants.ORDER_CANCELED]:
            serializer = OrderSerializer(order)
            publishment = serializer.data

            topic = constants.TOPIC_HISTORY.format(pair=order.pair, type=order.type)

            client = get_crossbar_client()
            client.publish(topic, **publishment)

    def offers_notification(order):
        """
            Send websocket notification to the router if offers is changed.
        """

        orders = Order.objects.filter(pair=order.pair, type=order.type, price=order.price)

        amount = sum((offer.amount for offer in orders))
        total = sum((offer.total for offer in orders))

        topic = constants.TOPIC_OFFERS.format(pair=order.pair, type=order.type)

        publishment = {
            "amount": str(amount),
            "total": str(total),
            "pair": order.pair,
            "type": order.type,
            "price": str(order.price)
        }

        client = get_crossbar_client()
        client.publish(topic, **publishment)

    order = instance
    history_notification(order)
    offers_notification(order)


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
