__author__ = 'andrew.shvv@gmail.com'

from rest_framework.status import HTTP_201_CREATED

from absortium.tests.base import AbsoritumUnitTest
from core.utils.logging import getLogger

logger = getLogger(__name__)


class TestViewTest(AbsoritumUnitTest):
    def test_test(self):
        data = {
            "amount": "132"
        }

        response = self.client.post('/api/tests/', data=data, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)
