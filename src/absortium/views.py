__author__ = 'andrew.shvv@gmail.com'

import psycopg2
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.db import utils
from psycopg2 import extensions
from rest_framework import generics, mixins, viewsets
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from absortium.celery import tasks


from absortium import constants
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
from absortium.utils import retry
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
    by the given order type and currency pair value.
    """

    serializer_class = OfferSerializer

    permission_classes = ()
    authentication_classes = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_fields = []

    def get_queryset(self):
        """
            This method used for filter origin offers queryset by the given order type and
            pair values that usually are coming from the url. See urls.py
        """
        filter = {}
        self.exclude_fields = []

        primary_currency = self.request.data['primary_currency']
        if primary_currency:
            primary_currency = primary_currency.lower()

            if primary_currency in constants.AVAILABLE_CURRENCIES.keys():
                primary_currency = constants.AVAILABLE_CURRENCIES[primary_currency]
                filter.update(primary_currency=primary_currency)
                self.exclude_fields.append('primary_currency')
        else:
            raise ValidationError("Not available currency type '{}'".format(primary_currency))

        secondary_currency = self.request.data['secondary_currency']
        if secondary_currency:
            secondary_currency = secondary_currency.lower()

            if secondary_currency in constants.AVAILABLE_CURRENCIES.keys():
                secondary_currency = constants.AVAILABLE_CURRENCIES[secondary_currency]
                filter.update(secondary_currency=secondary_currency)
                self.exclude_fields.append('secondary_currency')
        else:
            raise ValidationError("Not available currency '{}'".format(secondary_currency))

        return Offer.objects.filter(**filter).all()

    def get_serializer(self, *args, **kwargs):
        """
            This method used setting 'exclude_fields' parameter
            that was constructed in the 'get_queryset' method
        """
        return super().get_serializer(exclude_fields=self.exclude_fields, *args, **kwargs)

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


class AccountViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = AccountSerializer

    def get_queryset(self):
        return self.request.user.accounts.all()

    @init_account(pk_name="pk")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(self, request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(owner=self.request.user)


class DepositViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
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

    @init_account()
    @retry(times=1000, exceptions=(utils.OperationalError,
                                   extensions.TransactionRollbackError,
                                   utils.InternalError,
                                   psycopg2.OperationalError))
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Lock row until the end of transaction
            # https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-for-update
            account = Account.objects.select_for_update().get(pk=request.account.pk)
            deposit = serializer.save(account=account)

            amount = account.amount + deposit.amount
            account.update(amount=amount)

            return Response(serializer.data, status=HTTP_201_CREATED)


# @init_account()
# def create(self, request, *args, **kwargs):
#     serializer = self.get_serializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#     info = self.perform_create(serializer)
#
#     return Response(info, status=status.HTTP_201_CREATED)
#
# def perform_create(self, serializer):
#     # TODO: Change topik (pk) to some more secure and long number
#     context = {
#         "validated_data": serializer.validated_data,
#         "topic": str(self.request.user.pk),
#         "account_pk": self.request.account.pk
#     }
#     task = tasks.do_deposit.delay(**context)
#     return {"task_id": task.id}


class WithdrawalViewSet(mixins.CreateModelMixin,
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
    @retry(times=1000, exceptions=(
            utils.OperationalError, extensions.TransactionRollbackError, utils.InternalError,
            psycopg2.OperationalError))
    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Lock row until the end of transaction
            # https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-for-update
            account = Account.objects.select_for_update().get(pk=request.account.pk)
            deposit = serializer.save(account=account)

            if account.amount - deposit.amount >= 0:
                amount = account.amount - deposit.amount
                account.update(amount=amount)

                data = serializer.data
                return Response(data, status=HTTP_201_CREATED)

            else:
                raise ValidationError("Not enough money for withdrawal")


# @init_account()
# def create(self, request, *args, **kwargs):
#     serializer = self.get_serializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#
#     info = self.perform_create(serializer)
#     return Response(info, status=status.HTTP_201_CREATED)
#
# def perform_create(self, serializer):
#     # TODO: Change topik (pk) to some more secure and long number
#     context = {
#         "validated_data": serializer.validated_data,
#         "topic": str(self.request.user.pk),
#         "account_pk": self.request.account.pk
#     }
#     task = tasks.do_withdraw.delay(**context)
#     return {"task_id": task.id}


class ExchangeViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      # mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = ExchangeSerializer

    def __init__(self, *args, **kwargs):
        self.account = None
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return self.request.user.exchanges.all()

    # @init_account()
    # def destroy(self, request, *args, **kwargs):
    #     # TODO Celery queue
    #     super().destroy(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        context = {
            "data": request.data,
            "user_pk": request.user.pk,
        }

        async_result = tasks.do_exchange.delay(**context)
        exchange = async_result.get(propagate=True)
        logger.debug(exchange)
        return Response(exchange, status=HTTP_201_CREATED)


        # def create(self, request, *args, **kwargs):
        #     serializer = self.get_serializer(data=request.data)
        #     serializer.is_valid(raise_exception=True)
        #     exchange = serializer.save(owner_id=request.user.pk)
        #
        # context = {
        #     "exchange_pk": exchange.pk,
        # }
        #
        #
        # async_result = tasks.do_exchange.delay(**context)
        # logger.debug(async_result)
        # try:
        #     exchange_data = async_result.get(timeout=0.2, propagate=False)
        # except TimeoutError:
        #     return Response(serializer.validated_data)
        #
        # if isinstance(exchange_data, ValidationError):
        #     pass
        # elif isinstance(exchange_data, Exception):
        #     pass
        # else:
        #     logger.debug(exchange_data)
        #     return Response(exchange_data)


class TestViewSet(mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = TestSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save(owner_id=self.request.user.pk)
            instance = Test.objects.select_for_update().get(pk=instance.pk)
            instance = Test.objects.select_for_update().get(pk=instance.pk)
