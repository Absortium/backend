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

