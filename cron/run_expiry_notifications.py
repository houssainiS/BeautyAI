#!/usr/bin/env python3
import os
import sys
import django
import traceback

# ===== CONFIG =====
PROJECT_ROOT = "/webapps/beautyAI/BeautyAI"  # absolute path to your project root (where manage.py is)
VENV_PYTHON = "/webapps/beautyAI/venv/bin/python"  # your venv python (used by cron)
DJANGO_SETTINGS = "makeupAI_hosted.settings"
LOG_FILE = "/webapps/beautyAI/logs/cron.log"

# Add project root to Python path
sys.path.append(PROJECT_ROOT)

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS)

# Setup Django
try:
    django.setup()
except Exception as e:
    with open(LOG_FILE, "a") as f:
        f.write("[ERROR] Django setup failed:\n")
        f.write(traceback.format_exc() + "\n")
    sys.exit(1)

# Import your function after setup
from cron.send_usage_expiry_notifications import send_usage_expiry_notifications

# Run the notifications
if __name__ == "__main__":
    try:
        send_usage_expiry_notifications()
    except Exception as e:
        with open(LOG_FILE, "a") as f:
            f.write("[ERROR] send_usage_expiry_notifications failed:\n")
            f.write(traceback.format_exc() + "\n")
