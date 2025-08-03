from django.apps import AppConfig

class IncidentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.incidents'
    verbose_name = 'Incident Management'

    def ready(self):
        import apps.incidents.signals
