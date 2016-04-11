__author__ = 'andrew.shvv@gmail.com'

from redlock import Redlock
from tasks import deposit, add, User


class TaskManager():
    def __init__(self):
        self.locked = []
        self.dlm = Redlock([{"host": "absortium.com", "port": 6379, "db": 0}, ])

    def lock(self, user):
        return self.dlm.lock(user['id'], 1000)

    def unlock(self, user):
        self.dlm.unlock(user['id'])

    def is_locked(self, user):
        return user['id'] in self.locked


tm = TaskManager()

deposit.delay(user_id=0, currency='btc', money=1000)
deposit.delay(user_id=0, currency='btc', money=1000)

import time
time.sleep(2)
user = User.get(pk=0)
print(user)

# deposit.delay(tm, users[0], 'btc', 1000)
# deposit.delay(tm, users[0], 'btc', 1000)
# deposit.delay(tm, users[0], 'btc', 1000)
# deposit.delay(tm, users[0], 'btc', 1000)
# deposit.delay(tm, users[1], 'btc', 1000)
