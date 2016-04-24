__author__ = 'andrew.shvv@gmail.com'

from celery import shared_task, Task
from django.db import transaction, connection
from django.db.utils import OperationalError

from absortium import constants
from absortium.model.locks import lockexchange, opposites
from absortium.model.models import Account
from absortium.serializer.serializers import ExchangeSerializer, WithdrawSerializer, DepositSerializer
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


class DBTask(Task):
    abstract = True

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        connection.close()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        connection.close()

    def on_success(self, retval, task_id, args, kwargs):
        connection.close()


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES, base=DBTask)
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


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES, base=DBTask)
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


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES, base=DBTask)
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
                    break

            if history:
                return history
            else:
                return [exchange]

        with transaction.atomic():
            with lockexchange(exchange):
                exchange.process_account()
                history = process(exchange)

            return [ExchangeSerializer(e).data for e in history]

    except OperationalError:
        raise self.retry(countdown=constants.CELERY_RETRY_COUNTDOWN)
