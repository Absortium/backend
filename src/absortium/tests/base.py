__author__ = 'andrew.shvv@gmail.com'

import time

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase, APIClient, APITransactionTestCase

from absortium import celery_app
from absortium.tests.mixins.account import CreateAccountMixin
from absortium.tests.mixins.coinbase import CoinbaseMockMixin
from absortium.tests.mixins.deposit import CreateDepositMixin
from absortium.tests.mixins.exchange import CreateExchangeMixin
from absortium.tests.mixins.router import RouterMockMixin
from absortium.tests.mixins.withdrawal import CreateWithdrawalMixin
from core.utils.logging import getLogger

logger = getLogger(__name__)


class AbsortiumTestMixin():
    def get_first(self, response):
        self.assertEqual(response.status_code, HTTP_200_OK)

        json = response.json()
        results = json['results']

        self.assertGreaterEqual(len(results), 0)

        return results[0]


class AbsoritumLiveTest(APITransactionTestCase,
                        AbsortiumTestMixin,
                        CreateAccountMixin,
                        CreateDepositMixin,
                        CreateExchangeMixin,
                        CoinbaseMockMixin,
                        CreateWithdrawalMixin):
    def setUp(self):
        super().setUp()

        self.mock_coinbase()
        self.client = APIClient()

    def tearDown(self):
        self.unmock_coinbase()

        super().tearDown()

    def wait_celery(self, tag=None):
        # WARNING: Sometime may skip the execution and I don't know why
        i = celery_app.control.inspect()

        def queue_not_empty():
            queues = i.active()

            if not queues:
                raise Exception("Celery was stopped!")

            queue_empty = True
            for name, tasks in queues.items():
                if tasks:
                    queue_empty = False

            if tag:
                logger.debug("Wait for '{}'...".format(tag, queue_empty))

            return not queue_empty

        # i.active() may return empty list but process is not over
        # so lets check several times :)

        times = 3
        while all([queue_not_empty() for _ in range(times)]):
            time.sleep(0.2)


@override_settings(CELERY_ALWAYS_EAGER=True)
class AbsoritumUnitTest(APITestCase,
                        AbsortiumTestMixin,
                        CreateAccountMixin,
                        CreateDepositMixin,
                        CreateExchangeMixin,
                        CreateWithdrawalMixin,
                        RouterMockMixin,
                        CoinbaseMockMixin):
    def setUp(self):
        User = get_user_model()
        user = User(username="primary")
        user.save()

        self.user = user
        self.client = APIClient()
        self.client.force_authenticate(user)

        self.mock_router()
        self.mock_coinbase()

        super().setUp()

    def tearDown(self):
        super().tearDown()

        self.unmock_router()
        self.unmock_coinbase()
