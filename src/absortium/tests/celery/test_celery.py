__author__ = 'andrew.shvv@gmail.com'

from absortium.tests.base import AbsortiumTest
from absortium.celery import app
from core.utils.logging import getLogger

logger = getLogger(__name__)


class CeleryTest(AbsortiumTest):
    def test_run(self, *args, **kwargs):
        app.do_deposit.delay()