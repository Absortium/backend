# import absolute imports from the future, so that our celery.py module
# will not clash with the library
from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from absortium.celery import app as celery_app  # noqa

default_app_config = 'absortium.apps.AbsortiumConfig'