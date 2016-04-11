__author__ = 'andrew.shvv@gmail.com'

from django.apps import AppConfig

class AbsortiumConfig(AppConfig):
    name = 'absortium'
    verbose_name = "Absortium"

    def ready(self):
        super(AbsortiumConfig, self).ready()

        # This will make sure the signals is always imported when
        # Django starts so that exclude import cycles
        import absortium.signals


        # This will make sure the app is always imported when
        # Django starts so that shared_task will use this app.
        from absortium.celery import app as celery_app  # noqa
