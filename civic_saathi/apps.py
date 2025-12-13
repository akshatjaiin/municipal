from django.apps import AppConfig


class CivicSaathiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "civic_saathi"

    def ready(self):
        # Import signals to register them
        import civic_saathi.signals  # noqa
