from django.apps import AppConfig


class TransformerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "transformer"

    def ready(self) -> None:
        from transformer import signals
