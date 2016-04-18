__author__ = 'andrew.shvv@gmail.com'

import decimal
import random
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

    def generate_users(self, n):
        username_length = 20
        User = get_user_model()
        contexts = {}
        for _ in range(n):
            random_username = ''.join([random.choice(ascii_letters) for _ in range(username_length)])
            user = User(username=random_username)
            user.save()
            contexts[user] = {}
        return contexts

    def create_accounts(self, contexts):
        for user, context in contexts.items():
            self.client.force_authenticate(user)
            btc_account_pk, _ = self.create_account('btc')
            eth_account_pk, _ = self.create_account('eth')
            contexts[user].update(btc_account_pk=btc_account_pk)
            contexts[user].update(eth_account_pk=eth_account_pk)

        return contexts

    def bombarding_deposit_withdrawal(self, contexts):
        n = 5

        for user, context in contexts.items():
            self.client.force_authenticate(user)
            random_deposits = [self.random_amount() for _ in range(n)]

            start_deposit = 0
            for deposit_amount in random_deposits:
                # In order to ensure that withdraw task is not failing because of run out of money we should init deposit
                self.create_deposit(context['btc_account_pk'], amount=deposit_amount, with_checks=False)
                start_deposit += deposit_amount

            random_withdrawals = random_deposits
            for deposit_amount, withdraw_amount in zip(random_deposits, random_withdrawals):
                self.create_deposit(context['btc_account_pk'], amount=deposit_amount, with_checks=False)
                self.create_withdrawal(context['btc_account_pk'], amount=withdraw_amount, with_checks=False)

            contexts[user].update({
                "real_amount": sum(random_deposits) - sum(random_withdrawals) + start_deposit
            })

        return contexts

    def bombarding_exchanges(self, contexts):
        n = 10

        for user, context in contexts.items():
            self.client.force_authenticate(user)
            random_deposits = [self.random_amount() for _ in range(n)]

            start_deposit = 0
            for deposit_amount in random_deposits:
                # In order to ensure that exchange task is not failing because of run out of money we should init deposit
                self.create_deposit(context['btc_account_pk'], amount=deposit_amount, with_checks=False)
                start_deposit += deposit_amount

            import time
            time.sleep(3)

            random_exchanges = random_deposits
            for deposit_amount, exchange_amount in zip(random_deposits, random_exchanges):
                self.create_exchange(context['btc_account_pk'], currency="eth", price="2.0", amount=exchange_amount,
                                     with_checks=False)

            contexts[user].update({
                "real_amount": sum(random_deposits) - sum(random_exchanges) + start_deposit
            })

        return contexts

    def check_accuracy(self, contexts):
        for user, context in contexts.items():
            account = Account.objects.get(pk=context['btc_account_pk'])
            logger.debug(u"User pk: {} \nAccount amount: {} \nReal amount: {}\n".format(user.pk,
                                                                                        account.amount,
                                                                                        context['real_amount']))
            self.assertEqual(context['real_amount'], account.amount)

    def test_withdraw_deposit(self, *args, **kwargs):
        """
            In order to execute this test celery worker should use django test db, for that set the CELERY_TEST=True
            environment variable in the worker(celery) service. See docker-compose.yml

        """
        users_count = 10

        contexts = self.generate_users(users_count)
        contexts = self.create_accounts(contexts)
        contexts = self.bombarding_deposit_withdrawal(contexts)

        # Wait for celery process all tasks
        # TODO: Use celery inspect module!
        import time
        time.sleep(4)

        self.check_accuracy(contexts)

    def test_exchanges(self, *args, **kwargs):
        """
            In order to execute this test celery worker should use django test db, for that set the CELERY_TEST=True
            environment variable in the worker(celery) service. See docker-compose.yml
        """

        users_count = 2

        contexts = self.generate_users(users_count)
        contexts = self.create_accounts(contexts)
        contexts = self.bombarding_exchanges(contexts)

        # Wait for celery process all tasks
        # TODO: Use celery inspect module!
        import time
        time.sleep(20)

        self.check_accuracy(contexts)
