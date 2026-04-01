from django.apps import AppConfig


class ClearanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clearance'

    def ready(self):
        import clearance.signals  # noqa: F401
