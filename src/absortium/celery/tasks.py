from datetime import timedelta

from django.utils import timezone

__author__ = 'andrew.shvv@gmail.com'

from celery import shared_task
from django.db import transaction
from django.db.utils import OperationalError

from absortium import constants
from absortium.celery.base import get_base_class
from absortium.crossbarhttp import publishment
from absortium.exceptions import AlreadyExistError
from absortium.model.locks import lockexchange, opposites
from absortium.model.models import Account, Exchange, MarketInfo
from absortium.serializer.serializers import \
    ExchangeSerializer, \
    WithdrawSerializer, \
    DepositSerializer, \
    AccountSerializer
from absortium.wallet.base import get_wallet_client
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES, base=get_base_class())
def do_deposit(self, *args, **kwargs):
    try:
        with transaction.atomic():
            data = kwargs['data']
            account_pk = kwargs['account_pk']

            serializer = DepositSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            account = Account.objects.select_for_update().get(pk=account_pk)
            deposit = serializer.save(account=account)

            deposit.process_account()

            return serializer.data

    except OperationalError:
        raise self.retry(countdown=constants.CELERY_RETRY_COUNTDOWN)


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES, base=get_base_class())
def do_withdrawal(self, *args, **kwargs):
    try:
        with transaction.atomic():
            data = kwargs['data']
            account_pk = kwargs['account_pk']

            serializer = WithdrawSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            account = Account.objects.select_for_update().get(pk=account_pk)
            withdrawal = serializer.save(account=account)

            withdrawal.process_account()

            return serializer.data

    except OperationalError:
        raise self.retry(countdown=constants.CELERY_RETRY_COUNTDOWN)


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES, base=get_base_class())
def do_exchange(self, *args, **kwargs):
    data = kwargs['data']
    user_pk = kwargs['user_pk']

    try:
        serializer = ExchangeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        exchange = serializer.object(owner_id=user_pk)

        def process(exchange):
            history = []
            for opposite in opposites(exchange):
                with lockexchange(opposite):
                    if exchange > opposite:
                        (completed, exchange) = exchange - opposite
                        history.append(completed)

                    elif exchange < opposite:
                        """
                            In this case exchange will be in the EXCHANGE_COMPLETED status, so just break loop and
                            than add exchange to the history
                        """
                        (_, opposite) = opposite - exchange
                        break

                    else:
                        """
                            In this case exchange will be in the EXCHANGE_COMPLETED status, so just break loop and
                            than add exchange to the history
                        """
                        (_, exchange) = exchange - opposite
                        break

            return history + [exchange]

        with publishment.atomic():
            with transaction.atomic():
                with lockexchange(exchange):
                    exchange.process_account()
                    history = process(exchange)

                return [ExchangeSerializer(e).data for e in history]

    except OperationalError:
        raise self.retry(countdown=constants.CELERY_RETRY_COUNTDOWN)


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES, base=get_base_class())
def create_account(self, *args, **kwargs):
    data = kwargs['data']
    user_pk = kwargs['user_pk']

    with publishment.atomic():
        serializer = AccountSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        account = serializer.object(owner_id=user_pk)

        try:
            obj = Account.objects.filter(owner_id=user_pk, currency=account.currency).all()[0]
            data = AccountSerializer(obj).data
            raise AlreadyExistError(data)
        except IndexError:
            with transaction.atomic():
                client = get_wallet_client(currency=account.currency)
                account.address = client.create_address()
                account.save()
                return AccountSerializer(account).data


@shared_task(bind=True, base=get_base_class())
def calculate_market_info(self, *args, **kwargs):
    with publishment.atomic():
        with transaction.atomic():
            currencies = constants.AVAILABLE_CURRENCIES.values()
            pairs = [(fc, tc) for fc in currencies for tc in currencies if fc != tc]

            for from_currency, to_currency in pairs:
                # 1. Get exchanges for the last 24h.
                day_ago = timezone.now() - timedelta(hours=constants.MARKET_INFO_DELTA)
                exchanges_24h = Exchange.objects.filter(status=constants.EXCHANGE_COMPLETED,
                                                        from_currency=from_currency,
                                                        to_currency=to_currency,
                                                        created__gt=day_ago).all()
                info = MarketInfo()
                info.from_currency = from_currency
                info.to_currency = to_currency

                rate_24h_max = 0
                rate_24h_min = 0
                volume_24h = 0
                if exchanges_24h:
                    rates = [exchange.price for exchange in exchanges_24h]

                    # 2. Get max rate.
                    rate_24h_max = max(rates)

                    # 3. Get min rate.
                    rate_24h_min = min(rates)

                    # 4. Calculate the market volume.
                    volume_24h = sum((exchange.amount for exchange in exchanges_24h))

                info.rate_24h_max = rate_24h_max
                info.rate_24h_min = rate_24h_min
                info.volume_24h = volume_24h

                # 5. Get the open exchanges
                last_exchanges = Exchange.objects.filter(
                    status=constants.EXCHANGE_COMPLETED,
                    from_currency=from_currency,
                    to_currency=to_currency).all()[:constants.MARKET_INFO_COUNT_OF_EXCHANGES]

                price = 0
                if last_exchanges:
                    # 6. Calculate average price
                    price = sum([exchange.price for exchange in last_exchanges]) / len(last_exchanges)

                info.rate = price
                info.save()
