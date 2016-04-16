__author__ = 'andrew.shvv@gmail.com'

from mock import patch, Mock

from core.utils.logging import getLogger

logger = getLogger(__name__)


class RouterMockMixin():
    """
        RouterMockMixin substitute original crossbarhttp client and save all publishments in local variable,
        after that you can check is publishment was made and is publishment data is valid.
    """

    def __init__(self):
        # WARNING!: Be careful with names you may override variables in the class that inherit this mixin!
        self._router_client = None
        self._router_patcher = None

    def mock_router(self):
        self._router_client = MockClient()
        self._router_patcher = patch('absortium.crossbarhttp.client.Client', new=self._router_client)
        self._router_patcher.start()

    def unmock_router(self):
        self._router_patcher.stop()

    def get_publishments(self, topic):
        topics = self._router_client.topics
        return topics[topic]

    def get_publishment(self, topic):
        publishments = self.get_publishments(topic)
        return publishments[0]

    def get_publishment_by_task_id(self, topic, task_id):
        self.assertTrue(type(topic) == str)
        self.assertTrue(type(task_id) == str)

        for pubslishment in self.get_publishments(topic):
            if pubslishment['task_id'] == task_id:
                return pubslishment
        return None

    def is_published(self, topic):
        topics = self._router_client.topics
        return topic in topics


class MockClient(Mock):
    topics = {}

    def publish(self, topic, **publishment):
        if topic not in self.topics:
            self.topics[topic] = []

        self.topics[topic].append(publishment)
