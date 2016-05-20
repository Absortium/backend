__author__ = 'andrew.shvv@gmail.com'

from absortium.tests.base import AbsoritumLiveTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class AccuracyTest(AbsoritumLiveTest):
    def test_withdrawal_deposit(self, *args, **kwargs):
        """
            In order to execute this test celery worker should use django test db, for that you shoukd set
            the CELERY_TEST=True environment variable in the worker(celery) service. See docker-compose.yml
        """

        global tm
        tm = ThreadManager()

        users_count = 10
        n = 3

        contexts = self.init_users(users_count)
        # We should wait until all users account are created (they are creating in celery)
        self.wait_celery()

        contexts = self.init_accounts(contexts)

        contexts = self.init_deposits(contexts, n)
        self.wait_celery()

        contexts = self.bombarding_withdrawal_deposit(contexts, n)
        tm.start()
        tm.stop()

        self.wait_celery()

        try:
            self.check_accounts(contexts)
            self.check_offers()
        except AssertionError:
            logger.debug("AssertionError was raised!!!")
            input("Press Enter to continue...")
