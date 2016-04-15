__author__ = 'andrew.shvv@gmail.com'

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

from absortium import constants
from absortium.crossbarhttp.client import get_crossbar_client
from absortium.lockmanager import locker
from absortium.model.models import Account
from absortium.serializer.serializers import DepositSerializer

celery_logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=settings.CELERY_MAX_RETRIES)
@locker()
def do_deposit(self, *args, **kwargs):
    serializer = DepositSerializer()
    serializer.populate_with_valid_data(kwargs['validated_data'])

    client = get_crossbar_client(url=constants.ROUTER_URL)

    account = Account.objects.get(pk=kwargs['account_pk'])
    deposit = serializer.save(account=account)

    # update() is converted directly to an SQL statement; it doesn't call save() on the model
    # instances, and so the pre_save and post_save signals aren't emitted.
    amount = account.amount + deposit.amount
    Account.objects.filter(pk=kwargs['account_pk']).update(amount=amount)

    publishment = {
        "id": self.request.id,
        "status": "SUCCESS",
        "data": serializer.data
    }

    client.publish(kwargs['topic'], **publishment)
