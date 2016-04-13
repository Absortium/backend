__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import settings
from django.contrib.auth.models import User, Group
from rest_framework import generics, mixins, status, viewsets
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.response import Response

from absortium.constants import AVAILABLE_PAIRS, AVAILABLE_ORDER_TYPES
from absortium.model.models import Order, Offer, Address, Account
from absortium.permissions import IsOwnerOrReadOnly
from absortium.serializer.serializers import \
    UserSerializer, \
    GroupSerializer, \
    OrderSerializer, \
    OfferSerializer, \
    AddressSerializer, \
    AccountSerializer, \
    ExchangeSerializer
from absortium.wallet import bitcoin
from core.utils.logging import getLogger

logger = getLogger(__name__)


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


class OrderListView(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    generics.GenericAPIView):
    """
    API endpoint that allows orders to be viewed and created.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class OrderDetailView(mixins.RetrieveModelMixin,
                      generics.GenericAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


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

        order_type = self.kwargs.get('type')

        if order_type:
            order_type = order_type.lower()

            if order_type in AVAILABLE_ORDER_TYPES.keys():
                order_type = AVAILABLE_ORDER_TYPES[order_type]
                filter.update(type=order_type)
                self.exclude_fields.append('type')
        else:
            raise ValidationError("Not available order type '{}'".format(order_type))

        pair = self.kwargs.get('pair')

        if pair:
            pair = pair.lower()

            if pair in AVAILABLE_PAIRS.keys():
                pair = AVAILABLE_PAIRS[pair]
                filter.update(pair=pair)
                self.exclude_fields.append('pair')
        else:
            raise ValidationError("Not available currency pair '{}'".format(pair))

        return Offer.objects.filter(**filter).all()

    def get_serializer(self, *args, **kwargs):
        """
            This method used setting 'exclude_fields' parameter
            that was constructed in the 'get_queryset' method
        """
        return super().get_serializer(exclude_fields=self.exclude_fields, *args, **kwargs)

    def get(self, request, pair, type, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class AddressListView(mixins.CreateModelMixin,
                      generics.GenericAPIView):
    """
    API endpoint that allows address to be viewed and created.
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def post(self, request, currency, *args, **kwargs):
        if currency == 'btc':
            response = bitcoin.create_address(account_id=settings.COINBASE_ACCOUNT_ID)
            coinbase_data = response['data']
            data = request.data.copy()

            data['currency'] = currency
            data['address'] = coinbase_data['address']

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        return ValidationError("We do not support such currency as '{}'".format(currency))

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class MoneyView(mixins.ListModelMixin,
                mixins.DestroyModelMixin,
                generics.GenericAPIView):
    """
    API endpoint that allows address to be viewed and created.
    """

    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def post(self, request, currency, *args, **kwargs):
        pass


class AccountViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = AccountSerializer
    permission_classes = (IsOwnerOrReadOnly,)

    def check_account(self, account_pk):
        try:
            account = Account.objects.get(pk=account_pk)
        except Account.DoesNotExist:
            raise NotFound("Could not found account: {}".format(account_pk))

        if account.owner != self.request.user:
            raise PermissionDenied("You are not owner of this account.")

    def get_queryset(self):
        return self.request.user.accounts.all()

    def retrieve(self, request, *args, **kwargs):
        account_pk = self.kwargs.get('pk')
        self.check_account(account_pk)

        super().retrieve(self, request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ExchangeViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      mixins.DestroyModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = ExchangeSerializer

    def __init__(self, *args, **kwargs):
        self.account = None
        super().__init__(*args, **kwargs)

    def init_account(self, account_pk):
        try:
            account = Account.objects.get(pk=account_pk)
        except Account.DoesNotExist:
            raise NotFound("Could not found account: {}".format(account_pk))

        if account.owner != self.request.user:
            raise PermissionDenied("You are not owner of this account.")

        self.request.account = account

    def get_queryset(self):
        return self.request.account.exchanges.all()

    def perform_create(self, serializer):
        serializer.save(account=self.request.account)

    def destroy(self, request, *args, **kwargs):
        account_pk = self.kwargs.get('accounts_pk')
        self.init_account(account_pk)

        super().destroy(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        account_pk = self.kwargs.get('accounts_pk')
        self.init_account(account_pk)

        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        account_pk = self.kwargs.get('accounts_pk')
        self.init_account(account_pk)

        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        logger.debug(self.kwargs)
        account_pk = self.kwargs.get('accounts_pk')

        self.init_account(account_pk)
        return super().create(request, *args, **kwargs)
