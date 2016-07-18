__author__ = "andrew.shvv@gmail.com"

from absortium.crossbarhttp import publishment
from absortium.crossbarhttp.client import get_crossbar_client

from core.utils.logging import getLogger
from services.backend.absortium.tests import AbsoritumUnitTest

logger = getLogger(__name__)


class PublishmentsTest(AbsoritumUnitTest):
    def test_publishments_atomic_with_exception(self):
        """
            Check publishemnt.atomic context manager. If exception was raised inside the block
            than publishments should not be published.
        """

        try:
            with publishment.atomic():
                client = get_crossbar_client()
                client.publish("sometopic", text="sometext")

                raise Exception("Something wrong!")
        except Exception:
            pass

        self.assertEqual(self.get_publishments("sometopic"), None)

    def test_publishments_atomic_without_exception(self):
        """
            Check publishemnt.atomic context manager. If exception was raised inside the block
            than publishments should not be published.
        """

        with publishment.atomic():
            client = get_crossbar_client()
            client.publish("sometopic", text="sometext")
            self.assertEqual(self.get_publishments("sometopic"), None)

        self.assertNotEqual(self.get_publishments("sometopic"), None)
