__author__ = 'andrew.shvv@gmail.com'

import json
from urllib.parse import parse_qsl

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from requests_oauthlib import OAuth1

from jwtauth.models import Social


class SocialBackend():
    name = None
    user_name_map = None
    profile_name_map = None
    auth_type = None

    def __init__(self):
        if self.name is None:
            raise NotImplemented('You should specify "name" of the parameter')

        if self.user_name_map is None:
            raise NotImplemented('You should specify "user_name_map" parameter')

        if self.profile_name_map is None:
            raise NotImplemented('You should specify "profile_name_map" parameter')

        if self.auth_type is None:
            raise NotImplemented('You should specify "auth_type" parameter')

    def process(self, params):
        return params

    def get_profile(self, token):
        raise NotImplemented()

    def get_user_profile(self, profile):
        return {self.user_name_map[key]: value
                for key, value in profile.items()
                if key in self.user_name_map}

    def get_social_profile(self, profile):
        social_profile = {self.profile_name_map[key]: value
                          for key, value in profile.items()
                          if key in self.profile_name_map}
        social_profile['provider'] = self.name
        return social_profile

    def should_continue(self, params):
        if 'provider' not in params or params.get('provider') != self.name:
            return False

        if 'auth_type' not in params or params.get('auth_type') != self.auth_type:
            return False

        del params['provider']
        return True

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class OAuth2SocialBackend(SocialBackend):
    access_token_url = None
    user_api_url = None
    auth_type = "oauth2"

    def __init__(self):
        super().__init__()

        if self.access_token_url is None:
            raise NotImplemented('You should specify "access_token_url" parameter')

        if self.user_api_url is None:
            raise NotImplemented('You should specify "access_token_url" parameter')

    def get_token(self, credentials):
        raise NotImplemented()

    def authenticate(self, **params):
        # Skip authentication if wrong 'provider' or 'auth_type'
        if not self.should_continue(params):
            return None

        credentials = self.process(params)

        # Step 1. Exchange authorization code for access token.
        token = self.get_token(credentials)

        # Step 2. Retrieve information about the current user.
        profile = self.get_profile(token)

        # Step 3. Map profiles names into our names
        user_profile = self.get_user_profile(profile)
        social_profile = self.get_social_profile(profile)

        # Step 4. Search system user by provider id
        try:
            social = Social.objects.get(**social_profile)
        except Social.DoesNotExist:
            # Step 5. Create user if ot exist
            social = Social(**social_profile)

            User = get_user_model()
            user = User(**user_profile)
            user.save()

            social.user = user
            social.save()

        return social.user


class GoogleOAuth2(OAuth2SocialBackend):
    access_token_url = 'https://accounts.google.com/o/oauth2/token'
    user_api_url = 'https://www.googleapis.com/plus/v1/people/me/openIdConnect'
    name = "google"

    user_name_map = {
        'given_name': 'first_name',
        'family_name': 'last_name',
        'email': 'email',
        'name': 'username'
    }
    profile_name_map = {
        'sub': 'provider_uid'
    }

    def process(self, params):
        credentials = params.copy()
        credentials['client_secret'] = getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')
        credentials['grant_type'] = 'authorization_code'
        return credentials

    def get_token(self, credentials):
        r = requests.post(self.access_token_url, data=credentials)
        token = json.loads(r.text)
        return token

    def get_profile(self, token):
        headers = {'Authorization': 'Bearer {0}'.format(token['access_token'])}
        r = requests.get(self.user_api_url, headers=headers)
        profile = json.loads(r.text)
        return profile


class GithubOAuth2(OAuth2SocialBackend):
    access_token_url = 'https://github.com/login/oauth/access_token'
    user_api_url = 'https://api.github.com/user'
    name = "github"

    user_name_map = {
        'login': 'username',
        'email': 'email',
    }

    profile_name_map = {
        'id': 'provider_uid'
    }

    def process(self, params):
        credentials = params.copy()
        credentials['client_secret'] = getattr(settings, 'SOCIAL_AUTH_GITHUB_OAUTH2_SECRET')
        credentials['grant_type'] = 'authorization_code'
        return credentials

    def link_user(self):
        pass
        # # Step 3. (optional) Link accounts.
        # if request.headers.get('Authorization'):
        #     user = User.query.filter_by(github=profile['id']).first()
        #     if user:
        #         response = jsonify(message='There is already a GitHub account that belongs to you')
        #         response.status_code = 409
        #         return response
        #
        #     payload = parse_token(request)
        #
        #     user = User.query.filter_by(id=payload['sub']).first()
        #     if not user:
        #         response = jsonify(message='User not found')
        #         response.status_code = 400
        #         return response
        #
        #     u = User(github=profile['id'], display_name=profile['name'])
        #     db.session.add(u)
        #     db.session.commit()
        #     token = create_token(u)
        #     return jsonify(token=token)

    def get_profile(self, token):
        headers = {'User-Agent': 'Satellizer'}
        r = requests.get(self.user_api_url, params=token, headers=headers)
        profile = json.loads(r.text)
        profile['id'] = str(profile['id'])
        return profile

    def get_token(self, credentials):
        r = requests.get(self.access_token_url, params=credentials)
        token = dict(parse_qsl(r.text))
        return token


class OAuth1SocialBackend(SocialBackend):
    access_token_url = None
    auth_type = "oauth1"

    def __init__(self):
        super().__init__()

        if self.access_token_url is None:
            raise NotImplemented('You should specify "access_token_url" parameter')

    def authenticate(self, **params):
        # Skip authentication if wrong 'provider' or 'auth_type'
        if not self.should_continue(params):
            return None

        # Step 1. Generate credentials by params
        credentials = self.process(params)

        # Step 2. Get profile by credentials
        profile = self.get_profile(credentials)

        # Step 3. Map profiles and user names into our names
        user_profile = self.get_user_profile(profile)
        social_profile = self.get_social_profile(profile)

        # Step 4. Search system user by provider profile
        try:
            social = Social.objects.get(**social_profile)
        except Social.DoesNotExist:
            # Step 5. Create user if ot exist
            social = Social(**social_profile)

            User = get_user_model()
            user = User(**user_profile)
            user.save()

            social.user = user
            social.save()

        return social.user


class TwitterOAuth1(OAuth1SocialBackend):
    """
        TwitterOAuth1 backend used for retrieving information about twitter user and create system
        user if there is no twitter user in the system already.
        WARNING: Used only after 'oauth_token', 'oauth_verifier' was received in the view.
    """
    access_token_url = 'https://api.twitter.com/oauth/access_token'
    name = "twitter"

    user_name_map = {
        'screen_name': 'username',
        'email': 'email',
    }

    profile_name_map = {
        'user_id': 'provider_uid'
    }

    def process(self, params):
        credentials = {
            'client_key': getattr(settings, 'SOCIAL_AUTH_TWITTER_OAUTH1_KEY'),
            'client_secret': getattr(settings, 'SOCIAL_AUTH_TWITTER_OAUTH1_SECRET'),
            'resource_owner_key': params['oauth_token'],
            'verifier': params['oauth_verifier'],
        }
        return credentials

    def get_profile(self, credentials):
        auth = OAuth1(**credentials)
        r = requests.post(self.access_token_url, auth=auth)
        profile = dict(parse_qsl(r.text))
        return profile
