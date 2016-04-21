__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth.models import User, Group
from django.db import transaction
from rest_framework import generics, mixins, viewsets
from rest_framework import status
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.response import Response

from absortium import constants
from absortium.celery import tasks
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
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        info = self.perform_create(serializer)

        return Response(info, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        # TODO: Change topik (pk) to some more secure and long number
        context = {
            "validated_data": serializer.validated_data,
            "topic": str(self.request.user.pk),
            "account_pk": self.request.account.pk
        }
        task = tasks.do_deposit.delay(**context)
        return {"task_id": task.id}


class WithdrawViewSet(mixins.CreateModelMixin,
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
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        info = self.perform_create(serializer)
        return Response(info, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        # TODO: Change topik (pk) to some more secure and long number
        context = {
            "validated_data": serializer.validated_data,
            "topic": str(self.request.user.pk),
            "account_pk": self.request.account.pk
        }
        task = tasks.do_withdraw.delay(**context)
        return {"task_id": task.id}


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
        return self.request.account.ins.all() | self.request.account.outs.all()

    # @init_account()
    # def destroy(self, request, *args, **kwargs):
    #     # TODO Celery queue
    #     super().destroy(request, *args, **kwargs)

    @init_account()
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @init_account()
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @init_account()
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: We should do it in some another place, or furthermore we should create special field for Exchange currency
        account_currency = request.account.currency
        input_currency = serializer.validated_data['currency']

        if input_currency == account_currency:
            raise ValidationError("Exchange on the same currency does not make sense")

        serializer.validated_data['from_account_id'] = request.account.pk
        try:
            to_account = Account.objects.values("pk").get(owner__pk=request.user.pk, currency=input_currency)
        except Account.DoesNotExist:
            raise ValidationError("Account with '{}' currency doesn't exist".format(input_currency))

        serializer.validated_data['to_account_id'] = to_account['pk']

        context = {
            "validated_data": serializer.validated_data,
            "topic": str(self.request.user.pk),
        }

        async_result = tasks.do_exchange.delay(**context)
        logger.debug(async_result)
        try:
            result = async_result.get(timeout=0.2, propagate=False)
        except TimeoutError:
            result = None

        status = async_result.status

        if isinstance(result, Exception):
            traceback = async_result.traceback

            logger.debug(status)
            # Task was created and handled but some errors are happened
            return Response({'status': status, 'error': str(result), 'traceback': traceback})

        elif result is None:
            id_ = async_result.id

            # Task was created and but not yet handled
            return Response({"id": id_, 'status': status})

        else:
            # Task was created and handled successfully
            return Response({'result': result, 'status': status})


class TestViewSet(mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = TestSerializer

    def perform_create(self, serializer):
        logger.debug("TEST PERFORM CREATE START")
        with transaction.atomic():
            instance = serializer.save(owner_id=self.request.user.pk)
            instance = Test.objects.select_for_update().get(pk=instance.pk)
            instance = Test.objects.select_for_update().get(pk=instance.pk)

        logger.debug("TEST PERFORM CREATE FINISH")
