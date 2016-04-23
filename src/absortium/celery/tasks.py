__author__ = 'andrew.shvv@gmail.com'

from celery import shared_task, Task
from django.db import transaction, connection
from django.db.utils import OperationalError

from absortium import constants
from absortium.model.locks import lockexchange, opposites
from absortium.serializer.serializers import ExchangeSerializer
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


#
# @shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES)
# def do_deposit(self, *args, **kwargs):
#     try:
#         with transaction.atomic():
#             serializer = DepositSerializer()
#             serializer.populate_with_valid_data(kwargs['validated_data'])
#
#             # Lock row until the end of transaction
#             # https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-for-update
#             account = Account.objects.select_for_update().get(pk=kwargs['account_pk'])
#             deposit = serializer.save(account=account)
#
#             amount = account.amount + deposit.amount
#
#             # update() is converted directly to an SQL statement; it doesn't call save() on the model
#             # instances, and so the pre_save and post_save signals aren't emitted.
#             Account.objects.filter(pk=kwargs['account_pk']).update(amount=amount)
#
#         data = serializer.data
#         data['status'] = "COMPLETED"
#         publishment = {
#             "task_id": self.request.id,
#             "action": "deposit",
#             "data": data,
#         }
#
#         client = get_crossbar_client()
#         client.publish(kwargs['topic'], **publishment)
#     except OperationalError:
#         raise self.retry(countdown=constants.CELERY_RETRY_COUNTDOWN)


# @shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES)
# def do_withdraw(self, *args, **kwargs):
#     try:
#         with transaction.atomic():
#             serializer = WithdrawSerializer()
#             serializer.populate_with_valid_data(kwargs['validated_data'])
#
#             # Lock row until the end of transaction
#             # https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-for-update
#             account = Account.objects.select_for_update().get(pk=kwargs['account_pk'])
#             deposit = serializer.save(account=account)
#
#             publishment = {
#                 "task_id": self.request.id,
#                 "action": "withdrawal"
#             }
#
#             if account.amount - deposit.amount >= 0:
#                 amount = account.amount - deposit.amount
#                 # update() is converted directly to an SQL statement; it doesn't call save() on the model
#                 # instances, and so the pre_save and post_save signals aren't emitted.
#                 Account.objects.filter(pk=kwargs['account_pk']).update(amount=amount)
#
#                 data = serializer.data
#                 data['status'] = "COMPLETED"
#                 publishment.update({
#                     "data": data,
#                 })
#
#             else:
#                 data = serializer.data
#                 data['status'] = "REJECTED"
#                 publishment.update({
#                     "data": data,
#                     "reason": "Not enough money for withdrawal",
#                 })
#
#                 raise ValidationError("Not enough money for withdrawal")
#
#         client = get_crossbar_client()
#         client.publish(kwargs['topic'], **publishment)
#     except OperationalError:
#         raise self.retry(countdown=constants.CELERY_RETRY_COUNTDOWN)


class DBTask(Task):
    abstract = True

    def after_return(self, *args, **kwargs):
        connection.close()


@shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES, base=DBTask)
def do_exchange(self, *args, **kwargs):
    exchange = None

    data = kwargs['data']
    user_pk = kwargs['user_pk']

    try:
        serializer = ExchangeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        exchange = serializer.object(owner_id=user_pk)

        with transaction.atomic():
            with lockexchange(exchange):

                exchange.check_account()

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

# @shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES)
# def do_check_users(self, *args, **kwargs):
#     User = get_user_model()
#     users = User.objects.all()
#
#     if not users:
#         celery_logger.info("There is no users")
#
#     for user in users:
#         celery_logger.info("\nUser username: {}".format(user.username))
#
#
# @shared_task(bind=True, max_retries=constants.CELERY_MAX_RETRIES)
# def do_check_accounts(self, *args, **kwargs):
#     accounts = Account.objects.all()
#
#     if not accounts:
#         celery_logger.info("There is no accounts")
#
#     for account in accounts:
#         celery_logger.info("\nUser pk: {}\n Amount: {}".format(account.owner.pk, account.amount))
