__author__ = 'andrew.shvv@gmail.com'

from mock import patch, MagicMock

from core.utils.logging import getLogger

logger = getLogger(__name__)

topics = {}


class RouterMockMixin():
    """
        RouterMockMixin substitute original crossbarhttp client and save all publishments in local variable,
        after that you can check- is publishment was made and is publishment data is valid.
    """

    def mock_router(self):

        mock = MagicMock(return_value=MockClient())
        self._router_patcher = patch('absortium.crossbarhttp.client.Client', new=mock)
        self._router_patcher.start()

    def unmock_router(self):
        self._router_patcher.stop()

    def get_publishments(self, topic=None):
        global topics

        if topic is None:
            return topics
        else:
            try:
                return topics[topic]
            except KeyError:
                return None

    def publishments_flush(self):
        global topics
        topics = {}

    def get_publishment(self, topic):
        publishments = self.get_publishments(topic)
        if publishments:
            return publishments[0]
        else:
            return None

    def get_publishment_by_task_id(self, task_id):
        global topics

        self.assertTrue(type(task_id) == str)

        for _, publishments in topics.items():
            for pubslishment in publishments:
                if 'task_id' in pubslishment and pubslishment['task_id'] == task_id:
                    return pubslishment
        return None

    def is_published(self, topic):
        global topics
        return topic in topics


class MockClient():
    def publish(self, topic, **publishment):
        global topics
        if topic not in topics:
            topics[topic] = []

        topics[topic].append(publishment)
