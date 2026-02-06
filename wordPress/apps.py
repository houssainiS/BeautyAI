from django.apps import AppConfig


class WordpressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wordPress'

    def ready(self):
        import wordPress.models