from django.db import models


from django.utils.timezone import now

class Visitor(models.Model):
    # Unique visitor per day
    session_key = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=50)
    date = models.DateField(default=now)

    class Meta:
        unique_together = ('session_key', 'date')  # Prevent duplicates for same day

    def __str__(self):
        return f"{self.ip_address} on {self.device_type} at {self.date}"


class FaceAnalysis(models.Model):
    # Total visits (every request)
    session_key = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=50)
    domain = models.CharField(max_length=255, null=True, blank=True)  # 👈 Added field
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address} visited {self.domain or 'unknown'} on {self.timestamp}"


class Feedback(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'

    FEEDBACK_CHOICES = [
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    ]

    feedback_type = models.CharField(max_length=10, choices=FEEDBACK_CHOICES)
    dislike_reason = models.TextField(blank=True, null=True)  # only for dislikes
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.feedback_type} at {self.created_at}"

class AllowedOrigin(models.Model):
    url = models.URLField(unique=True, help_text="Allowed Shopify store URL")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url
    

####webhook models#######

from django.db import models

class Shop(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    offline_token = models.TextField(blank=True, null=True)  # Permanent token
    online_token = models.TextField(blank=True, null=True)   # Short-lived token
    installed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # Track active/inactive status
    theme_editor_link = models.URLField(blank=True, null=True)  # Store Theme Editor deep link
    metafield_definition_id = models.CharField(max_length=255, blank=True, null=True)  # 👈 Store definition ID

    def __str__(self):
        return self.domain



class PageContent(models.Model):
    title = models.CharField(max_length=200, default="Face Analyzer")
    body = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


#### notifciation system ####
from django.utils import timezone

class Purchase(models.Model):
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    order_id = models.CharField(max_length=255, null=True, blank=True)
    product_id = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    purchase_date = models.DateTimeField(default=timezone.now)
    usage_duration_days = models.IntegerField(default=0)
    notified = models.BooleanField(default=False)
    domain = models.CharField(max_length=255, null=True, blank=True)

    def expiry_date(self):
        return self.purchase_date + timezone.timedelta(days=self.usage_duration_days)

