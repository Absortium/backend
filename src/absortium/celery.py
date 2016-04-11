from __future__ import absolute_import

__author__ = 'andrew.shvv@gmail.com'

import os

from celery import Celery

# Specifying the settings here means the celery command
# line program will know where your Django project is.
# This statement must always appear before the app instance is created.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'absortium.settings')

from django.conf import settings  # noqa



app = Celery('absortium', broker=settings.CELERY_BROKER)

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
#
# from redlock import Redlock
#
# class TaskManager():
#     def __init__(self):
#         self.locked = []
#         self.dlm = Redlock([{"host": "docker.lockmanager", "port": 6379, "db": 0}, ])
#
#     def lock(self, user):
#         return self.dlm.lock(user['id'], 1000)
#
#     def unlock(self, user):
#         self.dlm.unlock(user['id'])
#
#     def is_locked(self, user):
#         return user['id'] in self.locked
#
# from absortium.models import Address
#
# @app.task(acks_late=True)
# def deposit(user_id, currency, money):
#     # lock = tm.lock(user)
#     # if lock:
#     user = User.get(pk=user_id)
#
#     print("=" * 30)
#     print("User id: {}".format(user['id']))
#     print("User name: {}".format(user['name']))
#     user['money'][currency] += money
#     # tm.unlock(user)
#     # else:
#     #     raise Reject('user is locked', requeue=True)
#     User.save(user=user)
#     return
#     print(user)
#
