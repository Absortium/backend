from __future__ import absolute_import

__author__ = 'andrew.shvv@gmail.com'

import os

from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'absortium.settings')
app = Celery('absortium')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

from redlock import Redlock
# from absortium.model.models import Account


class LockManager():
    def __init__(self):
        self.locked = []
        self.dlm = Redlock([{"host": settings.REDLOCK_URL, "port": 6379, "db": 0}])

    def lock(self, account_pk):
        return self.dlm.lock(account_pk, 10000000)

    def unlock(self, account_pk):
        self.dlm.unlock(account_pk)


from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

_lock_manager = None


def get_lock_manager():
    global _lock_manager
    if not _lock_manager:
        _lock_manager = LockManager()
    return _lock_manager


def locker(retry_countdown=settings.CELERY_RETRY_COUNTDOWN):
    lock_manager = get_lock_manager()

    def wrapper(func):
        def decorator(self, account_pk, *args, **kwargs):
            lock = lock_manager.lock(account_pk)
            logger.info(lock)
            if lock:
                func(self, account_pk, *args, **kwargs)
                lock_manager.unlock(lock)
            else:
                raise self.retry(countdown=retry_countdown)

        return decorator

    return wrapper


# import time


@app.task(bind=True, max_retries=settings.CELERY_MAX_RETRIES)
@locker()
def do_deposit(self, account_pk):
    logger.info("DEPOSIT!")
    # account = Account.objects.get(pk=account_pk)
    # deposit = serializer.save(account=account)
    #
    # logger.debug(account)
    # logger.debug(deposit)
    #
    # # # update() is converted directly to an SQL statement; it doesn't call save() on the model
    # # # instances, and so the pre_save and post_save signals aren't emitted.
    # amount = account.amount + deposit.amount
    # Account.objects.filter(pk=account.pk).update(amount=amount)
