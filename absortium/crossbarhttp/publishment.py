__author__ = 'andrew.shvv@gmail.com'

from services.backend.absortium.crossbarhttp.client import set_crossbar_client, get_crossbar_client


class atomic:
    """
        Replace real client with mock one and consume all publishments which was made during block execution. Then
        if exceptions was not raised - publish them with real client.
    """

    topics = None
    client = None

    def __enter__(self):
        self.topics = {}
        self.client = get_crossbar_client()
        set_crossbar_client(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            for topic, publishments in self.topics.items():
                for publishment in publishments:
                    self.client.publish(topic, **publishment)

        set_crossbar_client(self.client)

    def publish(self, topic, **publishment):
        if not topic in self.topics:
            self.topics[topic] = []
        self.topics[topic].append(publishment)
