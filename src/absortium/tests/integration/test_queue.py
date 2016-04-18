__author__ = 'andrew.shvv@gmail.com'

import decimal
import random
from string import ascii_letters

from django.contrib.auth import get_user_model

from absortium import constants
from absortium.celery import tasks
from absortium.model.models import Account
from absortium.tests.base import AbsoritumLiveTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class BenchmarkTest(AbsoritumLiveTest):
    before_dot = 10 ** (constants.MAX_DIGITS - constants.DECIMAL_PLACES) - 1
    after_dot = 10 ** constants.DECIMAL_PLACES - 1

    def random_amount(self):
        amount = -1
        while amount < constants.AMOUNT_MIN_VALUE:
            amount = decimal.Decimal('%d.%d' % (random.randint(0, self.before_dot), random.randint(0, self.after_dot)))
        return amount

    def test_benchmark(self, *args, **kwargs):
        users_count = 10
        username_length = 20
        number_of_deposit = 30
        number_of_withdrawals = 10

        User = get_user_model()
        contexts = {}
        for _ in range(users_count):
            random_username = ''.join([random.choice(ascii_letters) for _ in range(username_length)])
            user = User(username=random_username)
            user.save()
            contexts[user] = {}

        tasks.do_check_users.delay()

        for user, context in contexts.items():
            self.client.force_authenticate(user)
            account_pk, _ = self.create_account('btc')
            contexts[user].update(account_pk=account_pk)

        for user, context in contexts.items():
            self.client.force_authenticate(user)

            random_deposits = [self.random_amount() for _ in range(number_of_deposit)]
            random_withdrawals = [self.random_amount() for _ in range(number_of_withdrawals)]

            for amount in random_deposits:
                self.create_deposit(account_pk=context['account_pk'], amount=amount, with_checks=False)

            for amount in random_withdrawals:
                self.create_withdrawal(account_pk=context['account_pk'], amount=amount, with_checks=False)

            contexts[user].update({
                "deposits": random_deposits,
                "withdrawals": random_withdrawals
            })

        import time
        time.sleep(5)

        for user, context in contexts.items():
            account = Account.objects.get(pk=context['account_pk'])
            real_amount = sum(context["deposits"]) - sum(context["withdrawals"])
            logger.debug(u"User pk: {} \nAccount amount: {} \nReal amount: {}\n".format(user.pk,
                                                                                        account.amount,
                                                                                        real_amount))
            if real_amount != account.amount:
                logger.debug("Inaccurancy!!")

        tasks.do_check_accounts.delay()

        import time
        time.sleep(1)
