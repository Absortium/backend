__author__ = 'andrew.shvv@gmail.com'

from django.contrib.auth import get_user_model
from mock import patch
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from jwtauth.models import Social


class SocialTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('jwtauth.backends.GoogleOAuth2.get_token', return_value="some_token")
    def test_google_auth(self, *args, **kwargs):
        data = {
            'code': '4/dLoDpyQkHc22Q9yS3gR-emF7uyV5ZZlsG07v1pLXupsx8',
            'client_id': '627422708179-p2nsu6pq24iatk3pccjdcj9gkq8lr1lj.apps.googleusercontent.com',
            'redirect_uri': 'http://absortium.com'
        }

        name = 'Andrew Samokhvalov'
        email = 'andrew.shvv@gmail.com'
        family_name = 'Samokhvalov'
        given_name = 'Andrew'
        sub = '1098765481728982'

        profile = {
            'email': email,
            'family_name': family_name,
            'given_name': given_name,
            'name': name,
            'sub': sub
        }

        with patch('jwtauth.backends.GoogleOAuth2.get_profile', return_value=profile) as _:
            response = self.client.post('/auth/social/oauth2/google', data=data, format='json')

            User = get_user_model()
            user = User.objects.first()

            self.assertEqual(User.objects.count(), 1)
            self.assertEqual(user.username, name)
            self.assertEqual(user.email, email)
            self.assertEqual(user.first_name, given_name)
            self.assertEqual(user.last_name, family_name)

            social = Social.objects.first()
            self.assertEqual(User.objects.count(), 1)
            self.assertEqual(social.user, user)
            self.assertEqual(social.provider, 'google')
            self.assertEqual(social.provider_uid, sub)
            self.assertEqual(social.user_id, user.id)

    @patch('jwtauth.backends.GithubOAuth2.get_profile', return_value="some_token")
    def test_github_auth(self, *args, **kwargs):
        data = {
            'code': '3b4282354ce046a08a3cf711',
            'client_id': '87ca9a8d2dc343578f622e5',
            'redirect_uri': 'http://absortium.com'
        }

        login = 'AndrewSamokhvalov'
        email = 'andrew.shvv@gmail.com'
        _id = '1098765481728982'

        profile = {
            'email': email,
            'login': login,
            'id': _id,
        }

        with patch('jwtauth.backends.GithubOAuth2.get_profile', return_value=profile) as _:
            response = self.client.post('/auth/social/oauth2/github', data=data, format='json')

            self.assertEqual(response.status_code, 200)

            User = get_user_model()
            user = User.objects.first()
            self.assertEqual(User.objects.count(), 1)
            self.assertEqual(user.username, login)
            self.assertEqual(user.email, email)

            social = Social.objects.first()
            self.assertEqual(User.objects.count(), 1)
            self.assertEqual(social.user, user)
            self.assertEqual(social.provider, 'github')
            self.assertEqual(social.provider_uid, _id)
            self.assertEqual(social.user_id, user.id)
