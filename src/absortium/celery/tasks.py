__author__ = 'andrew.shvv@gmail.com'

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.utils import OperationalError

from rest_framework.status import  HTTP_400_BAD_REQUEST

from absortium import constants
from absortium.crossbarhttp.client import get_crossbar_client
from absortium.exceptions import NotEnoughMoney
from absortium.model.locks import LockedExchange
from absortium.model.models import Account
from absortium.crossbarhttp import publishment
from absortium.serializer.serializers import DepositSerializer, WithdrawSerializer, ExchangeSerializer
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES)
def do_deposit(self, *args, **kwargs):
    try:
        with transaction.atomic():
            serializer = DepositSerializer()
            serializer.populate_with_valid_data(kwargs['validated_data'])

            # Lock row until the end of transaction
            # https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-for-update
            account = Account.objects.select_for_update().get(pk=kwargs['account_pk'])
            deposit = serializer.save(account=account)

            amount = account.amount + deposit.amount

            # update() is converted directly to an SQL statement; it doesn't call save() on the model
            # instances, and so the pre_save and post_save signals aren't emitted.
            Account.objects.filter(pk=kwargs['account_pk']).update(amount=amount)

        data = serializer.data
        data['status'] = "COMPLETED"
        publishment = {
            "task_id": self.request.id,
            "action": "deposit",
            "data": data,
        }

        client = get_crossbar_client()
        client.publish(kwargs['topic'], **publishment)
    except OperationalError:
        raise self.retry(countdown=constants.CELERY_RETRY_COUNTDOWN)


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES)
def do_withdraw(self, *args, **kwargs):
    try:
        with transaction.atomic():
            serializer = WithdrawSerializer()
            serializer.populate_with_valid_data(kwargs['validated_data'])

            # Lock row until the end of transaction
            # https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-for-update
            account = Account.objects.select_for_update().get(pk=kwargs['account_pk'])
            deposit = serializer.save(account=account)

            publishment = {
                "task_id": self.request.id,
                "action": "withdrawal"
            }

            if account.amount - deposit.amount >= 0:
                amount = account.amount - deposit.amount
                # update() is converted directly to an SQL statement; it doesn't call save() on the model
                # instances, and so the pre_save and post_save signals aren't emitted.
                Account.objects.filter(pk=kwargs['account_pk']).update(amount=amount)

                data = serializer.data
                data['status'] = "COMPLETED"
                publishment.update({
                    "data": data,
                })

            else:
                data = serializer.data
                data['status'] = "REJECTED"
                publishment.update({
                    "data": data,
                    "reason": "Not enough money for withdrawal",
                })

                raise NotEnoughMoney()

        client = get_crossbar_client()
        client.publish(kwargs['topic'], **publishment)
    except OperationalError:
        raise self.retry(countdown=constants.CELERY_RETRY_COUNTDOWN)


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES)
def do_exchange(self, *args, **kwargs):
    exchange = None

    try:
        # with publishment.atomic():
        with transaction.atomic():

            serializer = ExchangeSerializer()
            serializer.populate_with_valid_data(kwargs['validated_data'])
            exchange = serializer.save()
            exchange_pk = exchange.pk

            logger.info("Exchange pk: {} amount: {} from: {} to:{}".format(exchange.pk, exchange.amount,
                                                                           exchange.from_account.currency,
                                                                           exchange.currency))

            with LockedExchange(exchange_pk) as e1:
                # Check that we have enough money
                if e1.from_account.amount >= e1.amount:

                    # Subtract money from account because it is locked by exchange
                    e1.from_account.amount -= e1.amount
                else:
                    raise NotEnoughMoney()

                opposite_exchange_pks = e1.find_opposite()
                for opposite_exchange_pk in opposite_exchange_pks:

                    with LockedExchange(opposite_exchange_pk) as e2:
                        if e1 >= e2:
                            e1 -= e2
                        else:
                            e2 -= e1

                return ExchangeSerializer(e1).data

    except OperationalError:
        if exchange:
            logger.info("Discard exchange pk: {} amount: {} from: {} to:{}".format(exchange.pk, exchange.amount,
                                                                                   exchange.from_account.currency,
                                                                                   exchange.currency))
        raise self.retry(countdown=constants.CELERY_RETRY_COUNTDOWN)


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES)
def do_check_users(self, *args, **kwargs):
    User = get_user_model()
    users = User.objects.all()

    if not users:
        celery_logger.info("There is no users")

    for user in users:
        celery_logger.info("\nUser username: {}".format(user.username))


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES)
def do_check_accounts(self, *args, **kwargs):
    accounts = Account.objects.all()

    if not accounts:
        celery_logger.info("There is no accounts")

    for account in accounts:
        celery_logger.info("\nUser pk: {}\n Amount: {}".format(account.owner.pk, account.amount))
