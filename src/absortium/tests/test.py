__author__ = 'andrew.shvv@gmail.com'

from core.utils.logging import getLogger

logger = getLogger(__name__)

_client = None


def get_crossbar_client():
    global _client
    if not _client:
        _client = Client()
    return _client


def set_crossbar_client(client):
    global _client
    _client = client


class Client():
    def publish(self, topic, pubsliment):
        logger.debug("Topic: {} Publishment: {}".format(topic, pubsliment))


class Atomic():
    """
        Replace real client with mock one and consume all publishments which was made during block execution. Then
        if exceptions was not raised publish them with real client.
    """

    def __init__(self, *args, **kwargs):
        self.topics = {}
        self.client = get_crossbar_client()

    def publish(self, topic, publishment):
        if not topic in self.topics:
            self.topics[topic] = []
        self.topics[topic].append(publishment)

    def __enter__(self):
        set_crossbar_client(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            for topic, publishments in self.topics.items():
                for publishment in publishments:
                    self.client.publish(topic, publishment)

        if exc_type is NotEnoughMoney:
            self.client.publish("error topic", exc_val.msg)

        set_crossbar_client(self.client)


class NotEnoughMoney(Exception):
    msg = "Not enough money bitch!"

    def __init__(self, data):
        self.data = data


with Atomic():
    client = get_crossbar_client()
    client.publish("topic", "publishment1")
    client.publish("topic", "publishment2")
    client.publish("topic", "publishment3")
    logger.debug("AFTER PUBLISHMENT 1")
    # c = 1/0
    # c = "asdsa" + 1
    raise NotEnoughMoney("ASDASDASD")

logger.debug("AFTER PUBLISHMENT 2")