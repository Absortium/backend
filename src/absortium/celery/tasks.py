__author__ = 'andrew.shvv@gmail.com'

from celery import shared_task
from django.db import transaction
from django.db.utils import OperationalError, IntegrityError

from absortium.wallet.base import get_client
from absortium import constants
from absortium.celery.base import get_base_class
from absortium.exceptions import AlreadyExistError
from absortium.model.locks import lockexchange, opposites
from absortium.model.models import Account
from absortium.serializer.serializers import \
    ExchangeSerializer, \
    WithdrawSerializer, \
    DepositSerializer, \
    AccountSerializer
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
                    if exchange >= opposite:
                        (completed, exchange) = exchange - opposite
                        history.append(completed)
                    else:
                        (_, opposite) = opposite - exchange
                        history.append(exchange)

                if exchange.status == constants.EXCHANGE_COMPLETED:
                    return history

            if exchange.status == constants.EXCHANGE_INIT:
                return [exchange]

            elif exchange.status == constants.EXCHANGE_PENDING:
                history += [exchange]
                return history

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

    with transaction.atomic():
        serializer = AccountSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        account = serializer.object(owner_id=user_pk)

        try:
            client = get_client(currency=account.currency)
            account.address = client.create_address()
            account.save()
        except IntegrityError:
            obj = Account.objects.get(owner_id=user_pk, currency=account.currency)
            data = AccountSerializer(obj).data
            raise AlreadyExistError(data)
        return AccountSerializer(account).data
