__author__ = 'andrew.shvv@gmail.com'

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

from absortium import constants
from absortium.crossbarhttp.client import get_crossbar_client
from absortium.lockmanager import locker
from absortium.model.models import Account, Withdrawal
from absortium.serializer.serializers import DepositSerializer, WithdrawSerializer

celery_logger = get_task_logger(__name__)

from core.utils.logging import getLogger

django_logger = getLogger(__name__)


@shared_task(bind=True, max_retries=settings.CELERY_MAX_RETRIES)
@locker()
def do_deposit(self, *args, **kwargs):
    serializer = DepositSerializer()
    serializer.populate_with_valid_data(kwargs['validated_data'])

    account = Account.objects.get(pk=kwargs['account_pk'])
    deposit = serializer.save(account=account)

    # update() is converted directly to an SQL statement; it doesn't call save() on the model
    # instances, and so the pre_save and post_save signals aren't emitted.
    amount = account.amount + deposit.amount
    Account.objects.filter(pk=kwargs['account_pk']).update(amount=amount)

    publishment = {
        "task_id": self.request.id,
        "status": "SUCCESS",
        "data": serializer.data,
    }

    client = get_crossbar_client(url=constants.ROUTER_URL)
    client.publish(kwargs['topic'], **publishment)


@shared_task(bind=True, max_retries=settings.CELERY_MAX_RETRIES)
@locker()
def do_withdraw(self, *args, **kwargs):
    serializer = WithdrawSerializer()
    serializer.populate_with_valid_data(kwargs['validated_data'])

    account = Account.objects.get(pk=kwargs['account_pk'])
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

    client = get_crossbar_client(url=constants.ROUTER_URL)
    client.publish(kwargs['topic'], **publishment)
