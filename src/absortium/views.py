from absortium import constants

__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth.models import User, Group
from django.db import transaction
from rest_framework import generics, mixins, viewsets
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.status import HTTP_201_CREATED
from rest_framework.response import Response

from absortium.utils import get_currency
from absortium.celery import tasks
from absortium.mixins import CreateCeleryMixin
from absortium.model.models import Offer, Exchange, Account, MarketInfo
from absortium.serializer.serializers import \
    UserSerializer, \
    GroupSerializer, \
    OfferSerializer, \
    AccountSerializer, \
    ExchangeSerializer, \
    DepositSerializer, \
    WithdrawSerializer, \
    MarketInfoSerializer

from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


class UserList(generics.ListAPIView):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class OfferListView(mixins.ListModelMixin,
                    generics.GenericAPIView):
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
            This method used for filter origin offers queryset by the given from/to currency.
        """
        fields = {}

        to_currency = get_currency(self.request.GET, 'to_currency', throw=False)
        if to_currency is not None:
            fields.update(to_currency=to_currency)

        from_currency = get_currency(self.request.GET, 'from_currency', throw=False)
        if from_currency is not None:
            fields.update(from_currency=from_currency)

        return queryset.filter(**fields)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


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
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = AccountSerializer

    def get_queryset(self):
        return self.request.user.accounts.all()

    def list(self, request, *args, **kwargs):
        currency = get_currency(self.request.GET, 'currency', throw=False)
        queryset = self.filter_queryset(self.get_queryset())

        if currency is not None:
            queryset = queryset.filter(currency=currency).all()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @init_account(pk_name="pk")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def create_celery(self, request, *args, **kwargs):
        context = {
            "data": request.data,
            "user_pk": request.user.pk,
        }

        return tasks.create_account.delay(**context)

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(owner=self.request.user)


class DepositViewSet(mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = DepositSerializer

    def get_queryset(self):
        return self.request.account.deposits.all()

    @init_account()
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @init_account()
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class WithdrawalViewSet(CreateCeleryMixin,
                        mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = WithdrawSerializer

    def get_queryset(self):
        return self.request.account.withdrawals.all()

    @init_account()
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @init_account()
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @init_account()
    def create_celery(self, request, *args, **kwargs):
        context = {
            "data": request.data,
            "account_pk": request.account.pk,
        }

        return tasks.do_withdrawal.delay(**context)


class ExchangeViewSet(CreateCeleryMixin,
                      mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = ExchangeSerializer

    def __init__(self, *args, **kwargs):
        self.account = None
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return self.request.user.exchanges.all()

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create_celery(self, request, *args, **kwargs):
        context = {
            "data": request.data,
            "user_pk": request.user.pk,
        }

        return tasks.do_exchange.delay(**context)


class HistoryViewSet(generics.GenericAPIView,
                     mixins.ListModelMixin):
    serializer_class = ExchangeSerializer
    queryset = Exchange.objects.all()
    permission_classes = ()
    authentication_classes = ()

    def filter_queryset(self, queryset):
        """
            This method used for filter origin exchanges queryset by the given from/to currency.
        """
        fields = {"status": constants.EXCHANGE_COMPLETED}

        to_currency = get_currency(self.request.GET, 'to_currency', throw=False)
        if to_currency is not None:
            fields.update(to_currency=to_currency)

        from_currency = get_currency(self.request.GET, 'from_currency', throw=False)
        if from_currency is not None:
            fields.update(from_currency=from_currency)

        return queryset.filter(**fields)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class MarketInfoSet(mixins.ListModelMixin,
                    generics.GenericAPIView):
    serializer_class = MarketInfoSerializer
    queryset = MarketInfo.objects.all()
    permission_classes = ()
    authentication_classes = ()

    def list(self, request, *args, **kwargs):
        to_currency = get_currency(self.request.GET, 'to_currency', throw=False)
        from_currency = get_currency(self.request.GET, 'from_currency', throw=False)

        c1 = from_currency is not None
        c2 = to_currency is not None

        if c1 and c2:
            from_currency = [from_currency]
            to_currency = [to_currency]

        elif c1 and not c2:
            from_currency = [from_currency]
            to_currency = constants.AVAILABLE_CURRENCIES.values()

        elif not c1 and not c2:
            from_currency = constants.AVAILABLE_CURRENCIES.values()
            to_currency = constants.AVAILABLE_CURRENCIES.values()

        elif not c1 and c2:
            raise ValidationError("You should specify 'to_currency' field")

        count = self.request.GET.get('count')
        if not count:
            count = 1
        else:
            try:
                count = int(count)
            except ValueError:
                raise ValidationError("You should specify valid 'count' field")

        response = []
        for fc in from_currency:
            for tc in to_currency:
                if fc != tc:
                    if count == 0:
                        objs = self.get_queryset().filter(from_currency=fc, to_currency=tc)
                    else:
                        objs = self.get_queryset().filter(from_currency=fc, to_currency=tc)[:count]

                    serializer = self.get_serializer(objs, many=True)
                    response += serializer.data

        return Response(response)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


@api_view(http_method_names=['POST'])
@authentication_classes([])
@permission_classes([])
def notification_handler(request, currency, *args, **kwargs):
    data = request.data.copy()

    address = data.get('address')
    if address is None:
        raise ValidationError("'address' parameter should be specified")

    tx_hash = data.get('tx_hash')
    if tx_hash is None:
        raise ValidationError("'tx_hash' parameter should be specified")

    amount = data.get('amount')
    if amount is None:
        raise ValidationError("'amount' parameter should be specified")

    if address is None:
        raise ValidationError("Could not found address parameter in request")

    if currency:
        currency = currency.lower()

        if currency in constants.AVAILABLE_CURRENCIES.keys():
            currency = constants.AVAILABLE_CURRENCIES[currency]
            data.update(currency=currency)
        else:
            raise ValidationError("Not available currency '{}'".format(currency))
    else:
        raise ValidationError("'currency' should be specified in the url")

    try:
        account = Account.objects.get(currency=currency, address=address)
    except Account.DoesNotExist:
        raise NotFound("Could not found account with such address: {}".format(address))

    context = {
        "data": data,
        "account_pk": account.pk,
    }

    async_result = tasks.do_deposit.delay(**context)
    obj = async_result.get(propagate=True)
    return Response(obj, status=HTTP_201_CREATED)
