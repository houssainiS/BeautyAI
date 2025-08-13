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
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address} visited on {self.timestamp}"

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