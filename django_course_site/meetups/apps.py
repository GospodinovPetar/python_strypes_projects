from django.apps import AppConfig


class MeetupsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "meetups"

    def ready(self):
        # This line makes sure signals are registered
        import meetups.signals
