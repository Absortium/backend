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

required_docker_environments = {
    'SECRET_KEY': 'DJANGO_SECRET_KEY',

    'POSTGRES_PASSWORD': 'POSTGRES_PASSWORD',

    'ETH_NOTIFICATION_TOKEN': 'ETH_NOTIFICATION_TOKEN',
    'BTC_NOTIFICATION_TOKEN': 'BTC_NOTIFICATION_TOKEN',
    'WHOAMI': 'WHOAMI'
}

optional_docker_environments = {
    'AUTH0_SECRET_KEY': 'AUTH0_SECRET_KEY',
    'AUTH0_API_KEY': 'AUTH0_API_KEY',

    'COINBASE_API_KEY': 'COINBASE_API_KEY',
    'COINBASE_API_SECRET': 'COINBASE_API_SECRET',

    'ETHWALLET_API_KEY': 'ETHWALLET_API_KEY',
    'ETHWALLET_API_SECRET': 'ETHWALLET_API_SECRET',
    'CELERY_TEST': 'CELERY_TEST',

}

settings_module = sys.modules[__name__]
for name, env_name in optional_docker_environments.items():
    value = os.environ[env_name] if env_name in os.environ else None
    setattr(settings_module, name, value)

for name, env_name in required_docker_environments.items():
    value = os.environ[env_name] if env_name in os.environ else None
    if not value:
        raise NotImplementedError("Specify the '{}' environment variable.".format(env_name))
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
ETHWALLET_URL = "docker.ethwallet"

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
    'absortium.celery'

]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    )
}

ROOT_URLCONF = 'absortium.urls'

JWT_AUTH = {
    'JWT_DECODE_HANDLER': 'absortium.jwt.jwt_decode_handler',
    'JWT_PAYLOAD_GET_USERNAME_HANDLER': 'absortium.jwt.jwt_get_username_from_payload',
    'JWT_AUDIENCE': getattr(settings_module, 'AUTH0_API_KEY'),
    'JWT_SECRET_KEY': getattr(settings_module, 'AUTH0_SECRET_KEY'),
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',

}

WSGI_APPLICATION = 'wsgi.application'

# Very dirty hack for making celery to connect to the test_postgres db.
CELERY_TEST = getattr(settings_module, 'CELERY_TEST') == "True"
dbname = 'test_postgres' if CELERY_TEST else 'postgres'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': dbname,
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
