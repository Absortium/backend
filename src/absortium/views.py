from absortium import constants

__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth.models import User, Group
from django.db import transaction
from rest_framework import generics, mixins, viewsets
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from rest_framework.decorators import api_view
from rest_framework.status import HTTP_201_CREATED
from rest_framework.response import Response

from absortium.celery import tasks
from absortium.mixins import CreateCeleryMixin
from absortium.model.models import Offer, Account, Test
from absortium.serializer.serializers import \
    UserSerializer, \
    GroupSerializer, \
    OfferSerializer, \
    AccountSerializer, \
    ExchangeSerializer, \
    DepositSerializer, \
    WithdrawSerializer, \
    TestSerializer
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_fields = []

    def filter_queryset(self, queryset):
        """
            This method used for filter origin offers queryset by the given from/to currency.
        """
        fields = {}

        to_currency = self.request.data['to_currency']
        if to_currency:
            to_currency = to_currency.lower()

            if to_currency in constants.AVAILABLE_CURRENCIES.keys():
                to_currency = constants.AVAILABLE_CURRENCIES[to_currency]
                fields.update(to_currency=to_currency)
            else:
                raise ValidationError("Not available currency '{}'".format(to_currency))
        else:
            raise ValidationError("You should specify 'to_currency' field'")

        from_currency = self.request.data['from_currency']
        if from_currency:
            from_currency = from_currency.lower()

            if from_currency in constants.AVAILABLE_CURRENCIES.keys():
                from_currency = constants.AVAILABLE_CURRENCIES[from_currency]
                fields.update(from_currency=from_currency)
            else:
                raise ValidationError("Not available currency '{}'".format(from_currency))
        else:
            raise ValidationError("You should specify 'from_currency' field'")

        return queryset.filter(**fields)

    def get_serializer(self, *args, **kwargs):
        """
            This method used setting 'exclude_fields' parameter
            that was constructed in the 'get_queryset' method
        """
        return super().get_serializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):
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


class TestViewSet(mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = TestSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save(owner_id=self.request.user.pk)
            instance = Test.objects.select_for_update().get(pk=instance.pk)
            instance = Test.objects.select_for_update().get(pk=instance.pk)


@api_view(http_method_names=['POST'])
def notification_handler(request, currency, *args, **kwargs):
    # TODO: Make notification response async
    address = request.data.get('address')

    if not address:
        raise ValidationError("Could not found address parameter in request")

    if currency:
        currency = currency.lower()

        if currency in constants.AVAILABLE_CURRENCIES.keys():
            currency = constants.AVAILABLE_CURRENCIES[currency]
        else:
            raise ValidationError("Not available currency '{}'".format(currency))
    else:
        raise ValidationError("'currency' should be specified in the url'")

    try:
        for account in Account.objects.all():
            print(account.address)
        account = Account.objects.get(currency=currency, address=address)
    except Account.DoesNotExist:
        raise NotFound("Could not found account with such address: {}".format(address))

    request.data.update(currnecy=currency)
    context = {
        "data": request.data,
        "account_pk": account.pk,
    }

    async_result = tasks.do_deposit.delay(**context)
    obj = async_result.get(propagate=True)
    return Response(obj, status=HTTP_201_CREATED)
