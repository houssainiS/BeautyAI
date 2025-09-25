# cron/send_usage_expiry_notifications.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.utils import timezone
from recommender.models import Purchase  # import your Purchase model

# Hardcoded API key for testing (replace with env var in production)
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = "houssaini.hs@gmail.com"  # verified sender in SendGrid

def send_usage_expiry_notifications():
    """
    Check all purchases whose usage_duration has ended and send email via SendGrid API.
    """
    now = timezone.now()
    print(f"[DEBUG] Current time (UTC): {now}")

    purchases_to_notify = Purchase.objects.filter(notified=False)
    print(f"[DEBUG] Found {purchases_to_notify.count()} purchases to check")

    sg_client = SendGridAPIClient(SENDGRID_API_KEY)

    for purchase in purchases_to_notify:
        purchase_date = purchase.purchase_date
        if timezone.is_naive(purchase_date):
            purchase_date = timezone.make_aware(purchase_date, timezone.get_current_timezone())

        expiry = purchase_date + timezone.timedelta(days=purchase.usage_duration_days)
        print(f"[DEBUG] Checking purchase {purchase.id} for {purchase.email}")
        print(f"[DEBUG] Purchase date: {purchase_date}, Usage days: {purchase.usage_duration_days}, Expiry: {expiry}")

        if now >= expiry:
            subject = f"Your product '{purchase.product_name}' usage has ended"
            html_content = (
                f"<p>Hello,</p>"
                f"<p>Your usage duration for the product '<strong>{purchase.product_name}</strong>' has ended today.</p>"
                f"<p>Thank you for using our service!</p>"
            )
            message = Mail(
                from_email=FROM_EMAIL,
                to_emails=purchase.email,
                subject=subject,
                html_content=html_content
            )

            try:
                response = sg_client.send(message)
                print(f"[DEBUG] Email sent to {purchase.email}, Status Code: {response.status_code}")
                purchase.notified = True
                purchase.save()
            except Exception as e:
                print(f"[ERROR] Failed to send email to {purchase.email}: {e}")
        else:
            print(f"[DEBUG] Purchase {purchase.id} not yet expired.")
