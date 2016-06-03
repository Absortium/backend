from __future__ import absolute_import

__author__ = 'andrew.shvv@gmail.com'

import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'absortium.settings')

from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)

app = Celery('absortium',
             broker=settings.CELERY_BROKER,
             backend=settings.CELERY_RESULT_BACKEND)
if settings.MODE in ['frontend', 'integration']:
    """
        Because celery run in another process we should manually mock
        what we need when we test celery in integrity tests.
    """

    if settings.MODE == 'integration':
        from absortium.tests.mixins.celery import CeleryMockMixin
        CeleryMockMixin().mock_celery()
        logger.debug("Mock DBTask celery class")

    from absortium.tests.mixins.bitcoin import BitcoinClientMockMixin
    BitcoinClientMockMixin().mock_bitcoin_client()
    logger.debug("Mock Bitcoin client")

    from absortium.tests.mixins.ethereum import EthereumClientMockMixin
    EthereumClientMockMixin().mock_ethereum_client()
    logger.debug("Mock Ethereum client")

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
