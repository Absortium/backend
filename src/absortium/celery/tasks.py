__author__ = 'andrew.shvv@gmail.com'

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from absortium import constants
from absortium.crossbarhttp.client import get_crossbar_client
from absortium.model.locks import ExchangeLock, NotEnoughMoney
from absortium.model.models import Account
from absortium.serializer.serializers import DepositSerializer, WithdrawSerializer, ExchangeSerializer

celery_logger = get_task_logger(__name__)

from core.utils.logging import getLogger

django_logger = getLogger(__name__)


@shared_task(bind=True, max_retries=settings.CELERY_MAX_RETRIES)
def do_deposit(self, *args, **kwargs):
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

    publishment = {
        "task_id": self.request.id,
        "status": "SUCCESS",
        "action": "deposit",
        "data": serializer.data,
    }

    client = get_crossbar_client()
    client.publish(kwargs['topic'], **publishment)


@shared_task(bind=True, max_retries=settings.CELERY_MAX_RETRIES)
def do_withdraw(self, *args, **kwargs):
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

            publishment.update({
                "status": "SUCCESS",
                "data": serializer.data,
            })

        else:
            publishment.update({
                "status": "REJECTED",
                "reason": "Not enough money for withdrawal",
            })

    client = get_crossbar_client()
    client.publish(kwargs['topic'], **publishment)


@shared_task(bind=True, max_retries=settings.CELERY_MAX_RETRIES)
def do_exchange(self, *args, **kwargs):
    with transaction.atomic():
        serializer = ExchangeSerializer()
        serializer.populate_with_valid_data(kwargs['validated_data'])
        exchange_pk = serializer.save().pk

        with ExchangeLock(exchange_pk) as e1:
            try:
                # Check that we have enough money
                if e1.from_account.amount >= e1.amount:
                    e1.from_account.amount -= e1.amount
                else:
                    e1.status = constants.EXCHANGE_REJECTED
                    raise NotEnoughMoney()

                opposite_exchange_pks = e1.find_opposite()
                for opposite_exchange_pk in opposite_exchange_pks:
                    with ExchangeLock(opposite_exchange_pk) as e2:
                        if e1 >= e2:
                            e1 -= e2
                        else:
                            e2 -= e1

            except NotEnoughMoney:
                pass

            finally:
                data = ExchangeSerializer(e1).data

                publishment = {
                    "task_id": self.request.id,
                    "action": "exchange"
                }

                if e1.status == constants.EXCHANGE_REJECTED:
                    publishment.update({
                        "data": data,
                        "reason": "Not enough money on account"
                    })

                elif e1.status == constants.EXCHANGE_INIT:
                    publishment.update({
                        "data": data,
                        "reason": "There is no suitable exchanges right now waiting for incoming exchanges"
                    })
                elif e1.status == constants.EXCHANGE_PENDING:
                    publishment.update({
                        "data": data,
                        "reason": "There is no enough suitable exchanges right now waiting for incoming exchanges"
                    })

                elif e1.status == constants.EXCHANGE_COMPLETED:
                    publishment.update({
                        "data": data,
                        "reason": "Exchange completed successfully"
                    })

                client = get_crossbar_client()
                client.publish(kwargs['topic'], **publishment)


@shared_task(bind=True, max_retries=settings.CELERY_MAX_RETRIES)
def do_check_users(self, *args, **kwargs):
    User = get_user_model()
    users = User.objects.all()

    if not users:
        celery_logger.info("There is no users")

    for user in users:
        celery_logger.info("\nUser username: {}".format(user.username))


@shared_task(bind=True, max_retries=settings.CELERY_MAX_RETRIES)
def do_check_accounts(self, *args, **kwargs):
    accounts = Account.objects.all()

    if not accounts:
        celery_logger.info("There is no accounts")

    for account in accounts:
        celery_logger.info("\nUser pk: {}\n Amount: {}".format(account.owner.pk, account.amount))
