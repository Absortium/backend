__author__ = 'andrew.shvv@gmail.com'

from mock import patch, Mock
from rest_framework.test import APITestCase

from core.utils.logging import getLogger

logger = getLogger(__name__)


class LockManagerMixin(APITestCase):
    """
        LockManagerMixin substitute original lock manager and always return lock.
    """
    def __init__(self, *args, **kwargs):
        self.mock_lockmanager = None
        super().__init__(*args, **kwargs)

    def setUp(self):
        manager = MockLockManager()
        self.patcher = patch('absortium.lockmanager.LockManager', new=manager)
        self.mock_lockmanager = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        super().setUp()


class MockLockManager(Mock):
    topics = {}

    def __init__(self, *args, **kwargs):
        # self.mock_lock = object()
        super().__init__(*args, **kwargs)

    def lock(self, account_pk):
        return object()

    def unlock(self, lock):
        pass
