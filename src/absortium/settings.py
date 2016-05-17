"""
Django settings for absortium project.

Generated by 'django-admin startproject' using Django 1.9.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import sys

docker_environments = {
    'SECRET_KEY': 'DJANGO_SECRET_KEY',
    'SOCIAL_AUTH_GITHUB_OAUTH2_SECRET': 'SOCIAL_AUTH_GITHUB_OAUTH2_SECRET',
    'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET': 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET',
    'SOCIAL_AUTH_TWITTER_OAUTH1_SECRET': 'SOCIAL_AUTH_TWITTER_OAUTH1_SECRET',
    'SOCIAL_AUTH_TWITTER_OAUTH1_KEY': 'SOCIAL_AUTH_TWITTER_OAUTH1_KEY',
    'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',
    'COINBASE_API_KEY': 'COINBASE_API_KEY',
    'COINBASE_API_SECRET': 'COINBASE_API_SECRET',
    'ETH_NOTIFICATION_TOKEN': 'ETH_NOTIFICATION_TOKEN',
    'BTC_NOTIFICATION_TOKEN': 'BTC_NOTIFICATION_TOKEN',
    'CELERY_TEST': 'CELERY_TEST',
    'WHOAMI': 'WHOAMI'
}

settings_module = sys.modules[__name__]
for name, env_name in docker_environments.items():
    value = os.environ[env_name] if env_name in os.environ else None
    setattr(settings_module, name, value)

COINBASE_SANDBOX = True
if COINBASE_SANDBOX:
    COINBASE_API_URL = 'https://api.sandbox.coinbase.com'
else:
    COINBASE_API_URL = 'https://api.coinbase.com'

COINBASE_ACCOUNT_ID = '2bbf394c-193b-5b2a-9155-3b4732659ede'

CELERY_BROKER = 'amqp://guest@docker.celery.broker//'
CELERY_RESULT_BACKEND = 'redis://docker.celery.backend'

ROUTER_URL = "http://docker.router:8080/publish"
ETHCLIENT_URL = "docker.ethclient"

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django_extensions',
    'rest_framework',
    'absortium',
    'jwtauth',
    'absortium.celery'
]

AUTHENTICATION_BACKENDS = (
    'jwtauth.backends.GoogleOAuth2',
    'jwtauth.backends.GithubOAuth2',
    'jwtauth.backends.TwitterOAuth1',
    'django.contrib.auth.backends.ModelBackend',
)

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'jwtauth.authentication.JWTAuthentication',
    )
}

ROOT_URLCONF = 'absortium.urls'

JWT_AUTH = {
    'JWT_PAYLOAD_HANDLER': 'jwtauth.utils.wrapped_jwt_payload_handler',
}

WSGI_APPLICATION = 'wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

CELERY_TEST = getattr(settings_module, 'CELERY_TEST') == "True"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres' if not CELERY_TEST else 'test_postgres',
        'USER': 'postgres',
        'PASSWORD': getattr(settings_module, 'POSTGRES_PASSWORD'),
        'HOST': 'docker.postgres',
        'PORT': '5432',
        'CONN_MAX_AGE': 500
    }
}

SILENCED_SYSTEM_CHECKS = ["models.W001"]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True
