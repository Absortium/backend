__author__ = 'andrew.shvv@gmail.com'

from absortium.crossbarhttp.client import set_crossbar_client, get_crossbar_client
from absortium.exceptions import NotEnoughMoney


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
            self.client.publish(**exc_val.data)

        set_crossbar_client(self.client)


def atomic(*args, **kwargs):
    # Why create a function rather than just use Atomic? See django.db.transaction.atomic
    return Atomic(*args, **kwargs)
