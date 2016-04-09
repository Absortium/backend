__author__ = 'andrew.shvv@gmail.com'

from mock import patch
from rest_framework.test import APIClient
from rest_framework.test import APITestCase


class SerializerTrashInData(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('jwtauth.backends.GoogleOAuth2.get_token', return_value="some_token")
    def test_google_in_data(self, *args, **kwargs):
        data = {
            'codeTRASH': '4/dLoDpyQkHc22Q9yS3gR-emF7uyV5ZZlsG07v1pLXupsx8',
            'client_idTRASH': '627422708179-p2nsu6pq24iatk3pccjdcj9gkq8lr1lj.apps.googleusercontent.com',
            'redirect_uriTRASH': 'http://absortium.com'
        }

        response = self.client.post('/auth/social/oauth2/google', data=data, format='json')
        self.assertEqual(response.status_code, 400)

    @patch('jwtauth.backends.GoogleOAuth2.get_token', return_value="some_token")
    def test_google_trash_in_oauth_type(self, *args, **kwargs):
        data = {
            'code': '4/dLoDpyQkHc22Q9yS3gR-emF7uyV5ZZlsG07v1pLXupsx8',
            'client_id': '627422708179-p2nsu6pq24iatk3pccjdcj9gkq8lr1lj.apps.googleusercontent.com',
            'redirect_uri': 'http://absortium.com'
        }

        response = self.client.post('/auth/social/oauth2TRASH/google', data=data, format='json')
        self.assertEqual(response.status_code, 400)

    @patch('jwtauth.backends.GoogleOAuth2.get_token', return_value="some_token")
    def test_google_trash_in_provider(self, *args, **kwargs):
        data = {
            'code': '4/dLoDpyQkHc22Q9yS3gR-emF7uyV5ZZlsG07v1pLXupsx8',
            'client_id': '627422708179-p2nsu6pq24iatk3pccjdcj9gkq8lr1lj.apps.googleusercontent.com',
            'redirect_uri': 'http://absortium.com'
        }

        response = self.client.post('/auth/social/oauth2/googleTRASH', data=data, format='json')
        self.assertEqual(response.status_code, 400)
