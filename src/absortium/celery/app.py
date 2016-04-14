__author__ = 'andrew.shvv@gmail.com'

from celery import Celery

app = Celery('absortium', broker="amqp://guest@docker.broker//")


@app.task()
def do_deposit():
    print("Deposit!")


@app.task()
def do_withdrawal():
    print("Withdrawal!")


@app.task()
def do_exchange():
    print("Process exchange!")


@app.task()
def do_create_exchange():
    print("Create exchange!")
