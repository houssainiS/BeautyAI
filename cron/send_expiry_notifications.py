from django.core.management.base import BaseCommand
from cron.send_usage_expiry_notifications import send_usage_expiry_notifications

class Command(BaseCommand):
    help = "Send expiry emails for purchases"

    def handle(self, *args, **options):
        send_usage_expiry_notifications()
