__author__ = 'andrew.shvv@gmail.com'

from celery import shared_task, Task
from celery.signals import worker_process_init, worker_process_shutdown
from django.db import transaction, connection
from django.db.utils import OperationalError

from absortium import constants
from absortium.model.locks import lockexchange, opposites
from absortium.model.models import Account
from absortium.serializer.serializers import ExchangeSerializer, WithdrawSerializer, DepositSerializer
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


class DBTask(Task):
    # make task not visible
    abstract = True

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        # TODO: Should we really do this?!
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

        with transaction.atomic():
            with lockexchange(exchange):

                exchange.process_account()

                for opposite in opposites(exchange):

                    with lockexchange(opposite):
                        if exchange >= opposite:
                            exchange -= opposite
                        else:
                            opposite -= exchange

                    if exchange.amount == 0:
                        break

            return ExchangeSerializer(exchange).data

    except OperationalError:
        raise self.retry(countdown=constants.CELERY_RETRY_COUNTDOWN)
#
# db_conn = None
#
# @worker_process_init.connect
# def init_worker(**kwargs):
#     global db_conn
#     print('Initializing database connection for worker.')
#     db_conn = db.connect(DB_CONNECT_STRING)
#
#
# @worker_process_shutdown.connect
# def shutdown_worker(**kwargs):
#     global db_conn
#     if db_conn:
#         print('Closing database connectionn for worker.')
#         db_conn.close()