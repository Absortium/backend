__author__ = 'andrew.shvv@gmail.com'

import decimal
from string import ascii_letters

from django.contrib.auth import get_user_model

from absortium import constants
from absortium.model.models import Account
from absortium.tests.base import AbsoritumLiveTest
from core.utils.logging import getLogger

logger = getLogger(__name__)

from queue import Queue
from threading import Thread

import random


class ThreadQueue():
    threads = {}

    def __init__(self, num_worker_threads):
        self.num_worker_threads = num_worker_threads
        self.q = Queue()

    def _worker(self, name):
        while True:
            data = self.q.get()
            if data is None:
                break

            func = data["func"]
            args = data["args"]
            kwargs = data["kwargs"]

            # time.sleep(random.random())
            func(*args, **kwargs)
            self.q.task_done()

        logger.debug("Close session")
        from django import db
        db.connection.close()

    def add(self, func, *args, **kwargs):
        data = {
            "func": func,
            "args": args,
            "kwargs": kwargs
        }

        self.q.put(data)

    def start(self):
        for i in range(self.num_worker_threads):
            thread_name = "thread-{}".format(i)
            kwargs = {
                "name": thread_name
            }

            t = Thread(target=self._worker, kwargs=kwargs)
            t.quit = False
            t.start()
            self.threads[thread_name] = t

    def stop(self):
        for i in range(self.num_worker_threads):
            self.q.put(None)
        for t in self.threads:
            t.join()

    def block(self):
        # block until all tasks are done
        self.q.join()


progress_counter = 0


def django_thread_decorator(func):
    global tm

    def threaded_func(*args, **kwargs):
        global progress_counter
        try:
            func(*args, **kwargs)

            progress_counter += 1
            # logger.debug("Progress: {}".format(progress_counter))
        finally:
            from django.db import connection
            connection.close()

    def decorator(*args, **kwargs):
        global tm
        tm.add(threaded_func, *args, **kwargs)

    return decorator


class ThreadManager():
    threads = []

    def add(self, func, *args, **kwargs):
        t = Thread(target=func, args=args, kwargs=kwargs)
        self.threads.append(t)

    def start(self):
        for t in self.threads:
            t.start()

    def stop(self):
        for t in self.threads:
            t.join()


tq = None
pool = None
tm = None


class AccuracyTest(AbsoritumLiveTest):
    before_dot = 10 ** (constants.MAX_DIGITS - constants.DECIMAL_PLACES) - 1
    after_dot = 10 ** constants.DECIMAL_PLACES - 1

    def random_amount(self):
        amount = -1
        while amount < constants.AMOUNT_MIN_VALUE:
            amount = decimal.Decimal('%d.%d' % (random.randint(0, self.before_dot), random.randint(0, self.after_dot)))
        return amount

    def max_amounts(self, n=10):
        return [decimal.Decimal('%d.%d' % (self.before_dot, self.after_dot)) for _ in range(n)]

    def random_amounts(self, n=10):
        return [self.random_amount() for _ in range(n)]

    def init_users(self, n):
        username_length = 20
        User = get_user_model()
        contexts = {}
        for _ in range(n):
            random_username = ''.join([random.choice(ascii_letters) for _ in range(username_length)])
            user = User(username=random_username)
            user.save()
            contexts[user] = {}
        return contexts

    def init_accounts(self, contexts):
        for user, context in contexts.items():
            self.client.force_authenticate(user)
            btc_account_pk, _ = self.create_account('btc')
            eth_account_pk, _ = self.create_account('eth')
            context['btc_account_pk'] = btc_account_pk
            context['eth_account_pk'] = eth_account_pk

            context['btc'] = {}
            context['eth'] = {}

            context['btc']['deposits'] = []
            context['eth']['deposits'] = []

            context['btc']['withdrawals'] = []
            context['eth']['withdrawals'] = []

            context['btc']['exchanges'] = []
            context['eth']['exchanges'] = []

            contexts[user] = context

        return contexts

    def check_accuracy(self, contexts):
        for user, context in contexts.items():
            btc_deposits = context['btc']['deposits']
            btc_withdrawals = context['btc']['withdrawals']
            btc_exchanges = context['btc']['exchanges']

            eth_deposits = context['eth']['deposits']
            eth_withdrawals = context['eth']['withdrawals']
            eth_exchanges = context['eth']['exchanges']

            btc_real_amount = sum(btc_deposits) - sum(btc_withdrawals) - (sum(btc_exchanges) - sum(eth_exchanges))
            eth_real_amount = sum(eth_deposits) - sum(eth_withdrawals) - (sum(eth_exchanges) - sum(btc_exchanges))

            btc_account_amount = Account.objects.get(pk=context['btc_account_pk']).amount
            eth_account_amount = Account.objects.get(pk=context['eth_account_pk']).amount

            logger.debug(u"User pk: {} \n"
                         u"Account amount : {} BTC\n"
                         u"Real amount: {} BTC\n"
                         u"Account amount : {} ETH\n"
                         u"Real amount: {} ETH\n".format(user.pk,
                                                         btc_account_amount,
                                                         btc_real_amount,
                                                         eth_account_amount,
                                                         eth_real_amount))

            self.assertEqual(eth_real_amount, eth_account_amount)
            self.assertEqual(btc_real_amount, btc_account_amount)

    def init_deposits(self, contexts, n):
        """
            In order to ensure that exchange,withdraw tasks ate not failing because
            of run out of money we should firstly to deposit a lot of money on the accounts.
        """

        for user, context in contexts.items():
            random_deposits = self.max_amounts(n)

            for deposit_amount in random_deposits:
                self.create_deposit(context['btc_account_pk'], user=user, amount=deposit_amount, with_checks=False)
                self.create_deposit(context['eth_account_pk'], user=user, amount=deposit_amount, with_checks=False)
                self.create_deposit(context['btc_account_pk'], user=user, amount=deposit_amount, with_checks=False)
                self.create_deposit(context['eth_account_pk'], user=user, amount=deposit_amount, with_checks=False)

            context['btc']['deposits'] += 2 * random_deposits
            context['eth']['deposits'] += 2 * random_deposits
            contexts[user] = context
        return contexts

    @django_thread_decorator
    def threaded_create_deposit(self, *args, **kwargs):
        super().create_deposit(*args, **kwargs)

    @django_thread_decorator
    def threaded_create_exchange(self, *args, **kwargs):
        super().create_exchange(*args, **kwargs)

    @django_thread_decorator
    def threaded_create_withdrawal(self, *args, **kwargs):
        super().create_withdrawal(*args, **kwargs)

    def bombarding_withdrawal_deposit(self, contexts, n):
        for user, context in contexts.items():
            deposits = self.random_amounts(n)
            withdrawals = deposits
            exchanges = deposits

            amounts = list(zip(deposits, withdrawals, exchanges))
            for (d, w, e) in amounts:
                self.threaded_create_deposit(context['eth_account_pk'], user=user, amount=d, with_checks=False)

                self.threaded_create_withdrawal(context['eth_account_pk'], user=user, amount=d, with_checks=False)

                self.threaded_create_exchange(user=user,
                                              amount=e,
                                              from_currency="btc",
                                              to_currency="eth",
                                              price="1",
                                              with_checks=False)

                self.threaded_create_exchange(user=user,
                                              amount=e,
                                              from_currency="eth",
                                              to_currency="btc",
                                              price="1",
                                              with_checks=False)

            context['btc']['deposits'] += deposits
            context['btc']['withdrawals'] += withdrawals
            context['btc']['exchanges'] += exchanges

            context['eth']['deposits'] += deposits
            context['eth']['withdrawals'] += withdrawals
            context['eth']['exchanges'] += exchanges

            contexts[user] = context

        return contexts

    def test_withdrawal_deposit(self, *args, **kwargs):
        """
            In order to execute this test celery worker should use django test db, for that you shoukd set
            the CELERY_TEST=True environment variable in the worker(celery) service. See docker-compose.yml
        """
        global tm
        tm = ThreadManager()
        users_count = 20
        n = 1

        contexts = self.init_users(users_count)
        contexts = self.init_accounts(contexts)
        contexts = self.init_deposits(contexts, n)

        contexts = self.bombarding_withdrawal_deposit(contexts, n)
        tm.start()
        tm.stop()

        try:
            self.check_accuracy(contexts)
        except AssertionError:
            logger.debug("AssertionError was raised!!!")
            input("Press Enter to continue...")

    def test_multiprocess_withdrawal_deposit(self, *args, **kwargs):
        """
            In order to execute this test celery worker should use django test db, for that you shoukd set
            the CELERY_TEST=True environment variable in the worker(celery) service. See docker-compose.yml
        """

        from multiprocessing import Pool

        pool = Pool(processes=5)

        users_count = 1
        n = 1

        contexts = self.init_users(users_count)
        contexts = self.init_accounts(contexts)
        contexts = self.init_deposits(contexts, n)

        contexts = self.bombarding_withdrawal_deposit(contexts, n)
        pool.join()

        self.check_accuracy(contexts)
        pool.close()

        # def test_all(self, *args, **kwargs):
        #     """
        #         In order to execute this test celery worker should use django test db, for that you shoukd set
        #         the CELERY_TEST=True environment variable in the worker(celery) service. See docker-compose.yml
        #     """
        #
        #     users_count = 1
        #     operations = 10
        #     contexts = self.init_users(users_count)
        #     contexts = self.init_accounts(contexts)
        #     contexts = self.init_deposits(contexts, operations)
        #
        #     start = time.time()
        #
        #     contexts = self.bombarding_withdrawal_deposit_exchange(contexts, operations)
        #     self.wait_celery(tag="Bombarding tasks")
        #
        #     end = time.time()
        #     logger.debug("Info: {} seconds".format(end - start))
        #
        # try:
        #     self.check_accuracy(contexts)
        # except AssertionError:
        #     logger.debug("AssertionError was raised!!!")
        #     input("Press Enter to continue...")
