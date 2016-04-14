__author__ = 'andrew.shvv@gmail.com'

from absortium.celery import app
from absortium.tests.base import AbsortiumTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


import random

class CeleryTest(AbsortiumTest):
    def test_run(self, *args, **kwargs):

        for _ in range(0,1):
            account_pk = random.randint(0, 10)
            app.do_deposit.delay(account_pk)

        #TODO validate the amount of
