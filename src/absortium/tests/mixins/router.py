__author__ = 'andrew.shvv@gmail.com'

from mock import patch, MagicMock

from core.utils.logging import getLogger

logger = getLogger(__name__)

_topics = {}


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
        global _topics

        if topic is None:
            return _topics
        else:
            try:
                return _topics[topic]
            except KeyError:
                return None

    def publishments_flush(self):
        global _topics
        _topics = {}

    def get_publishment(self, topic):
        publishments = self.get_publishments(topic)
        if publishments:
            return publishments[0]
        else:
            return None

    def get_publishment_by_task_id(self, task_id):
        global _topics

        self.assertTrue(type(task_id) == str)

        for _, publishments in _topics.items():
            for pubslishment in publishments:
                if 'task_id' in pubslishment and pubslishment['task_id'] == task_id:
                    return pubslishment
        return None

    def is_published(self, topic):
        global _topics
        return topic in _topics


class MockClient():
    def publish(self, topic, **publishment):
        global _topics
        if topic not in _topics:
            _topics[topic] = []

        _topics[topic].append(publishment)
