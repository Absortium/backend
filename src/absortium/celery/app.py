__author__ = 'andrew.shvv@gmail.com'
import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'absortium.settings')
from django.conf import settings

app = Celery('absortium')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

class LockManager():
    pass

@app.task()
def do_deposit(account_pk):
    print("Deposit, account pk: {}".format(account_pk))


@app.task()
def do_withdrawal(account_pk):
    print("Withdrawal, account pk: {}".format(account_pk))


@app.task()
def do_exchange():
    print("Process exchange!")


@app.task()
def do_create_exchange():
    print("Create exchange!")
