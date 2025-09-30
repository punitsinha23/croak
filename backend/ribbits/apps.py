from django.apps import AppConfig


class RibbitsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ribbits'

    def ready(self):
        import ribbits.signals
