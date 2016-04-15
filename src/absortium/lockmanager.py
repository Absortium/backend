__author__ = 'andrew.shvv@gmail.com'

from django.conf import settings
from redlock import Redlock
from functools import wraps

def locker(retry_countdown=settings.CELERY_RETRY_COUNTDOWN):
    lock_manager = get_lock_manager()

    def wrapper(func):
        @wraps(func)
        def decorator(self, *args, **kwargs):
            account_pk = kwargs['account_pk']
            lock = lock_manager.lock(account_pk)
            if lock:
                func(self, account_pk, *args, **kwargs)
                lock_manager.unlock(lock)
            else:
                raise self.retry(countdown=retry_countdown)

        return decorator

    return wrapper


class LockManager():
    def __init__(self):
        self.locked = []
        self.dlm = Redlock([{"host": settings.REDLOCK_URL, "port": 6379, "db": 0}])

    def lock(self, account_pk):
        return self.dlm.lock(account_pk, 10000000)

    def unlock(self, account_pk):
        self.dlm.unlock(account_pk)


_lock_manager = None


def get_lock_manager():
    global _lock_manager
    if not _lock_manager:
        _lock_manager = LockManager()
    return _lock_manager
