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

    def check_accuracy(self, contexts):
        for user, context in contexts.items():
            account = Account.objects.select_for_update().get(pk=context['btc_account_pk'])
            logger.debug(u"User pk: {} \nAccount amount: {} \nReal amount: {}\n".format(user.pk,
                                                                                        account.amount,
                                                                                        context['real_amount']))
            self.assertEqual(context['real_amount'], account.amount)

    def bombarding_all(self, contexts):
        n = 20

        progress_counter = 0
        for user, context in contexts.items():
            self.client.force_authenticate(user)
            random_deposits = [self.random_amount() for _ in range(n)]

            deposits = 0
            withdrawals = 0
            exchanges = 0
            for deposit_amount in random_deposits:
                # In order to ensure that exchange task is not failing because of run out of money we should init deposit
                self.create_deposit(context['btc_account_pk'], amount=deposit_amount, with_checks=False)
                self.create_deposit(context['btc_account_pk'], amount=deposit_amount, with_checks=False)
                deposits += 2 * deposit_amount

            for deposit_amount in random_deposits:
                withdrawal_amount = deposit_amount
                exchange_amount = deposit_amount

                self.create_deposit(context['btc_account_pk'], amount=deposit_amount, with_checks=False)
                deposits += deposit_amount

                self.create_withdrawal(context['btc_account_pk'], amount=withdrawal_amount, with_checks=False)
                withdrawals += withdrawal_amount

                self.create_exchange(context['btc_account_pk'], currency="eth", amount=exchange_amount,
                                     with_checks=False)
                exchanges += exchange_amount

                progress_counter += 1

            logger.debug("Bombarding: {}/{}".format(progress_counter, len(random_deposits) * len(contexts.items())))

            contexts[user].update({
                "real_amount": deposits - withdrawals - exchanges
            })

        return contexts

    def test_exchanges(self, *args, **kwargs):
        """
            In order to execute this test celery worker should use django test db, for that set the CELERY_TEST=True
            environment variable in the worker(celery) service. See docker-compose.yml
        """

        users_count = 40

        contexts = self.generate_users(users_count)
        contexts = self.create_accounts(contexts)
        contexts = self.bombarding_all(contexts)

        self.wait_celery(tag="Check accuracy")

        self.check_accuracy(contexts)
