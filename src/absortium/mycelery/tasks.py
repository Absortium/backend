__author__ = 'andrew.shvv@gmail.com'

import time

from celery import Celery

app = Celery('tasks', broker='amqp://guest@absortium.com//')

users = {
    0: {
        'id': 0,
        'name': 'Andrey',
        'money': {
            'btc': 0,
            'eth': 0
        }
    },
    1: {
        'id': 2,
        'name': 'Ilia',
        'money': {
            'btc': 0,
            'eth': 0
        }
    },
    2: {
        'id': 3,
        'name': 'Igor',
        'money': {
            'btc': 0,
            'eth': 0
        }
    }
}


class User():
    @classmethod
    def get(cls, pk):
        global users
        return users[pk]

    @classmethod
    def save(cls, user):
        global users
        users[user['id']] = user

    @classmethod
    def all(cls, user):
        global users
        return users


@app.task(acks_late=True)
def deposit(user_id, currency, money):
    # lock = tm.lock(user)
    # if lock:
    user = User.get(pk=user_id)

    print("=" * 30)
    print("User id: {}".format(user['id']))
    print("User name: {}".format(user['name']))
    user['money'][currency] += money
    # tm.unlock(user)
    # else:
    #     raise Reject('user is locked', requeue=True)
    User.save(user=user)
    return
    print(user)


@app.task
def withdrawal(user, currency, money):
    time.sleep(0.5)
    if user['money'][currency] - money > 0:
        user['money'][currency] += money
    else:
        raise Exception()
    time.sleep(0.5)
    return user


@app.task
def exchange(first_user, second_user, first_order, second_order):
    time.sleep(0.5)


@app.task
def create_order(user, data):
    pass
    time.sleep(0.5)
    # return x + y


@app.task
def add(x, y):
    return x + y

# @task_prerun.connect()
# def task_prerun(signal=None, sender=None, task_id=None, task=None, args=None, kwargs=None):
#     print("Pre-run start")
#     time.sleep(3)
#     print("Pre-run end")
