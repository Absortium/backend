__author__ = 'andrew.shvv@gmail.com'

import decimal
import random
import time
from string import ascii_letters

from django.contrib.auth import get_user_model

from absortium import constants
from absortium.model.models import Account
from absortium.tests.base import AbsoritumLiveTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


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
            btc_account_pk, _ = self.get_account('btc')
            eth_account_pk, _ = self.get_account('eth')
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

            btc_real_amount = sum(btc_deposits) - sum(btc_withdrawals) - sum(btc_exchanges)
            eth_real_amount = sum(eth_deposits) - sum(eth_withdrawals) - sum(eth_exchanges)

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
            self.client.force_authenticate(user)
            random_deposits = self.max_amounts(n)

            for deposit_amount in random_deposits:
                self.create_deposit(context['btc_account_pk'], amount=deposit_amount, with_checks=False)
                self.create_deposit(context['eth_account_pk'], amount=deposit_amount, with_checks=False)

            context['btc']['deposits'] += random_deposits
            context['eth']['deposits'] += random_deposits
            contexts[user] = context
        return contexts

    def bombarding_withdrawal_deposit(self, contexts):

        progress_counter = 0
        for user, context in contexts.items():
            self.client.force_authenticate(user)

            deposits = self.random_amounts()
            withdrawals = deposits

            amounts = list(zip(deposits, withdrawals))
            for (d, w) in amounts:
                self.create_deposit(context['btc_account_pk'], amount=d, with_checks=False)
                self.create_deposit(context['eth_account_pk'], amount=d, with_checks=False)

                self.create_withdrawal(context['btc_account_pk'], amount=w, with_checks=False)
                self.create_withdrawal(context['eth_account_pk'], amount=w, with_checks=False)

                progress_counter += 1

            logger.debug("Bombarding: {}/{}".format(progress_counter, len(amounts) * len(contexts)))

            context['btc']['deposits'] += deposits
            context['btc']['withdrawals'] += withdrawals

            context['eth']['deposits'] += deposits
            context['eth']['withdrawals'] += withdrawals

            contexts[user] = context

        return contexts

    def bombarding_withdrawal_deposit_exchange(self, contexts, n):

        progress_counter = 0
        for user, context in contexts.items():
            self.client.force_authenticate(user)

            deposits = self.random_amounts(n)
            withdrawals = deposits
            exchanges = deposits

            amounts = list(zip(deposits, withdrawals, exchanges))
            for (d, w, e) in amounts:
                # self.create_deposit(context['btc_account_pk'], amount=d, with_checks=False)
                # self.create_deposit(context['eth_account_pk'], amount=d, with_checks=False)
                #
                # self.create_withdrawal(context['btc_account_pk'], amount=w, with_checks=False)
                # self.create_withdrawal(context['eth_account_pk'], amount=w, with_checks=False)

                self.create_exchange(price="1.0", amount=e, with_checks=False)
                self.create_exchange(price="1.0", amount=e, from_currency="eth", to_currency="btc", with_checks=False)

                progress_counter += 1

            logger.debug("Bombarding: {}/{}".format(progress_counter, len(amounts) * len(contexts)))

            # context['btc']['deposits'] += deposits
            # context['btc']['withdrawals'] += withdrawals
            # context['btc']['exchanges'] += exchanges

            # context['eth']['deposits'] += deposits
            # context['eth']['withdrawals'] += withdrawals
            # context['eth']['exchanges'] += exchanges

            contexts[user] = context

        return contexts

    def test_withdrawal_deposit(self, *args, **kwargs):
        """
            In order to execute this test celery worker should use django test db, for that you shoukd set
            the CELERY_TEST=True environment variable in the worker(celery) service. See docker-compose.yml
        """

        users_count = 100
        n = 5

        contexts = self.init_users(users_count)
        contexts = self.init_accounts(contexts)
        contexts = self.init_deposits(contexts, n)

        start = time.time()

        contexts = self.bombarding_withdrawal_deposit(contexts)
        self.wait_celery(tag="Bombarding tasks")

        end = time.time()
        logger.debug("Info: {} seconds".format(end - start))

        self.check_accuracy(contexts)

    def test_all(self, *args, **kwargs):
        """
            In order to execute this test celery worker should use django test db, for that you shoukd set
            the CELERY_TEST=True environment variable in the worker(celery) service. See docker-compose.yml
        """

        users_count = 1
        operations = 10
        contexts = self.init_users(users_count)
        contexts = self.init_accounts(contexts)
        contexts = self.init_deposits(contexts, operations)

        start = time.time()

        contexts = self.bombarding_withdrawal_deposit_exchange(contexts, operations)
        self.wait_celery(tag="Bombarding tasks")

        end = time.time()
        logger.debug("Info: {} seconds".format(end - start))

        try:
            self.check_accuracy(contexts)
        except AssertionError:
            logger.debug("AssertionError was raised!!!")
            input("Press Enter to continue...")
