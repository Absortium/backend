import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK

from absortium import constants
from absortium.celery import tasks
from absortium.mixins import \
    CreateCeleryMixin, \
    DestroyCeleryMixin, \
    ApproveCeleryMixin, \
    UpdateCeleryMixin, \
    LockCeleryMixin
from absortium.model.models import Offer, Order, Account, MarketInfo
from absortium.serializers import \
    OfferSerializer, \
    AccountSerializer, \
    OrderSerializer, \
    DepositSerializer, \
    WithdrawSerializer, \
    MarketInfoSerializer
from absortium.utils import get_field
from core.utils.logging import getPrettyLogger

__author__ = 'andrew.shvv@gmail.com'

logger = getPrettyLogger(__name__)


class OfferViewSet(viewsets.GenericViewSet):
    """
    This view should return a list of all offers
    by the given currencies.
    """

    serializer_class = OfferSerializer
    queryset = Offer.objects.all()
    permission_classes = ()
    authentication_classes = ()

    def filter_queryset(self, queryset):
        """
            This method used for filter origin offers queryset by the given pair/type currency.
        """
        fields = {}

        pair = get_field(self.request.GET, 'pair', constants.AVAILABLE_CURRENCY_PAIRS, throw=False)
        if pair is not None:
            fields.update(pair=pair)

        order_type = get_field(self.request.GET, 'type', constants.AVAILABLE_ORDER_TYPES, throw=False)
        if order_type is not None:
            fields.update(type=order_type)

        return queryset.filter(**fields)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.values("price", "type", "pair").annotate(amount=Sum('amount'))
        return HttpResponse(json.dumps(list(queryset), cls=DjangoJSONEncoder), content_type="application/json")


def init_account(pk_name="accounts_pk"):
    def wrapper(func):
        def decorator(self, request, *args, **kwargs):
            account_pk = self.kwargs.get(pk_name)

            try:
                account = Account.objects.get(pk=account_pk)
            except Account.DoesNotExist:
                raise NotFound("Could not found account: {}".format(account_pk))

            if account.owner != self.request.user:
                raise PermissionDenied("You are not owner of this account.")

            request.account = account
            return func(self, request, *args, **kwargs)

        return decorator

    return wrapper


class AccountViewSet(CreateCeleryMixin,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = AccountSerializer
    lookup_field = 'currency'

    def get_queryset(self):
        return self.request.user.accounts.all()

    def create_in_celery(self, request, *args, **kwargs):
        context = {
            "data": request.data,
            "user_pk": request.user.pk,
        }

        return tasks.create_account.delay(**context)


class DepositViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = DepositSerializer

    def get_queryset(self):
        return self.request.user.deposits.all()

    def filter_queryset(self, queryset):
        fields = {}

        currency = get_field(self.request.GET, 'currency', constants.AVAILABLE_CURRENCIES, throw=False)
        if currency is not None:
            fields.update(currency=currency)

        return queryset.filter(**fields)


class WithdrawalViewSet(CreateCeleryMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = WithdrawSerializer

    def get_queryset(self):
        return self.request.user.withdrawals.all()

    def filter_queryset(self, queryset):
        fields = {}

        currency = get_field(self.request.GET, 'currency', constants.AVAILABLE_CURRENCIES, throw=False)
        if currency is not None:
            fields.update(currency=currency)

        return queryset.filter(**fields)

    def create_in_celery(self, request, *args, **kwargs):
        context = {
            "data": request.data,
            "user_pk": request.user.pk,
        }

        return tasks.do_withdrawal.delay(**context)


class OrderViewSet(CreateCeleryMixin,
                   DestroyCeleryMixin,
                   ApproveCeleryMixin,
                   UpdateCeleryMixin,
                   LockCeleryMixin,
                   mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = OrderSerializer

    def __init__(self, *args, **kwargs):
        self.account = None
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return self.request.user.orders.all()

    def filter_queryset(self, queryset):
        """
            This method used for filter origin orders queryset by the given pair/type currency.
        """
        fields = {}

        pair = get_field(self.request.GET, 'pair', constants.AVAILABLE_CURRENCY_PAIRS, throw=False)
        if pair is not None:
            fields.update(pair=pair)

        order_type = get_field(self.request.GET, 'type', constants.AVAILABLE_ORDER_TYPES, throw=False)
        if order_type is not None:
            fields.update(type=order_type)

        return queryset.filter(**fields)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create_in_celery(self, request, *args, **kwargs):
        context = {
            "data": request.data,
            "user_pk": request.user.pk,
        }

        return tasks.create_order.delay(**context)

    def update_in_celery(self, request, *args, **kwargs):
        context = {
            "data": request.data,
            "order_pk": self.get_object().pk,
            "user_pk": request.user.pk,
        }

        return tasks.update_order.delay(**context)

    def approve_in_celery(self, request, *args, **kwargs):
        context = {
            "order_pk": self.get_object().pk,
            "user_pk": request.user.pk,
        }

        return tasks.approve_order.delay(**context)

    def destroy_in_celery(self, request, *args, **kwargs):
        context = {
            "order_pk": self.get_object().pk,
            "user_pk": request.user.pk,
        }

        return tasks.cancel_order.delay(**context)

    def lock_in_celery(self, request, *args, **kwargs):
        context = {
            "order_pk": self.get_object().pk,
            "user_pk": request.user.pk,
        }

        return tasks.lock_order.delay(**context)

    def unlock_in_celery(self, request, *args, **kwargs):
        context = {
            "order_pk": self.get_object().pk,
            "user_pk": request.user.pk,
        }

        return tasks.unlock_order.delay(**context)


class HistoryViewSet(viewsets.GenericViewSet,
                     mixins.ListModelMixin):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    permission_classes = ()
    authentication_classes = ()

    def filter_queryset(self, queryset):
        """
            This method used for filter origin orders queryset by the given pair/type currency.
        """
        fields = {'status': constants.ORDER_COMPLETED}

        pair = get_field(self.request.GET, 'pair', constants.AVAILABLE_CURRENCY_PAIRS, throw=False)
        if pair is not None:
            fields.update(pair=pair)

        order_type = get_field(self.request.GET, 'type', constants.AVAILABLE_ORDER_TYPES, throw=False)
        if order_type is not None:
            fields.update(type=order_type)

        return queryset.filter(**fields)


class MarketInfoSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = MarketInfoSerializer
    queryset = MarketInfo.objects.all()
    permission_classes = ()
    authentication_classes = ()

    def list(self, request, *args, **kwargs):
        fields = {}

        pair = get_field(self.request.GET, 'pair', constants.AVAILABLE_CURRENCY_PAIRS, throw=False)
        if pair is not None:
            fields.update(pair=pair)

        try:
            count = self.request.GET.get('count', 1)
            count = int(count)
        except ValueError:
            raise ValidationError("You should specify valid 'count' field")

        if count == 0:
            objs = self.get_queryset().filter(**fields)
        else:
            objs = self.get_queryset().filter(**fields)[:count]

        serializer = self.get_serializer(objs, many=True)
        return Response(serializer.data)


@api_view(http_method_names=['POST'])
@authentication_classes([])
@permission_classes([])
def btc_notification_handler(request, *args, **kwargs):
    if request.data.get('type') == constants.COINBASE_PAYMENT_NOTIFICATION:
        data = {}

        address = request.data.get('data').get('address')
        if address is None:
            raise ValidationError("'address' parameter should be specified")
        data['address'] = address

        amount = request.data.get('additional_data').get('amount').get('amount')
        if amount is None:
            raise ValidationError("'amount' parameter should be specified")
        data['amount'] = amount

        return base_notification_handler(constants.BTC, data)
    else:
        # Skip notification
        return Response(status=HTTP_200_OK)


@api_view(http_method_names=['POST'])
@authentication_classes([])
@permission_classes([])
def eth_notification_handler(request, *args, **kwargs):
    if request.data.get('address') is None:
        raise ValidationError("'address' parameter should be specified")

    if request.data.get('amount') is None:
        raise ValidationError("'amount' parameter should be specified")

    return base_notification_handler(constants.ETH, request.data)


def base_notification_handler(currency, data):
    try:
        account = Account.objects.get(currency=currency, address=data.get('address'))
    except Account.DoesNotExist:
        raise NotFound("Could not found account with such address: {}".format(data.get('address')))

    data['currency'] = currency

    context = {
        "data": data,
        "user_pk": account.owner.pk,
    }

    async_result = tasks.do_deposit.delay(**context)
    obj = async_result.get(propagate=True)
    return Response(obj, status=HTTP_201_CREATED)
