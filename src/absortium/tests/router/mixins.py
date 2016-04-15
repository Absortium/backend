__author__ = 'andrew.shvv@gmail.com'

from mock import patch, Mock
from rest_framework.test import APITestCase

from core.utils.logging import getLogger

logger = getLogger(__name__)


class RouterMixin(APITestCase):
    """
        RouterMixin substitute original crossbarhttp client and save all publishments in local variable,
        after that you can check is publishment was made and is publishment data is valid.
    """
    def __init__(self, *args, **kwargs):
        self.mock_client = None
        super().__init__(*args, **kwargs)

    def setUp(self):
        client = MockClient()
        self.patcher = patch('absortium.crossbarhttp.client.Client', new=client)
        self.mock_client = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        super().setUp()

    def get_publishments(self, topic):
        topics = self.mock_client.topics
        return topics[topic]

    def get_publishment(self, topic):
        publishments = self.get_publishments(topic)
        return publishments[0]

    def is_published(self, topic):
        topics = self.mock_client.topics
        return topic in topics


class MockClient(Mock):
    topics = {}

    def publish(self, topic, **publishment):
        if topic not in self.topics:
            self.topics[topic] = []

        self.topics[topic].append(publishment)
