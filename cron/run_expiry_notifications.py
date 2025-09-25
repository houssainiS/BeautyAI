#!/usr/bin/env python
import os
import sys
import django

# Add project root (where manage.py is) to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "makeupAI.settings")
django.setup()

from cron.send_usage_expiry_notifications import send_usage_expiry_notifications

if __name__ == "__main__":
    send_usage_expiry_notifications()
