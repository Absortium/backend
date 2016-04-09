__author__ = 'andrew.shvv@gmail.com'

from django.apps import AppConfig

class AbsortiumConfig(AppConfig):
    name = 'absortium'
    verbose_name = "Absortium"

    def ready(self):
        """
            In order to avoid cycle import problem we should
        """
        super(AbsortiumConfig, self).ready()
        import absortium.signals
