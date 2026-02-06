from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

class Plan(models.Model):
    PLAN_CHOICES = [('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')]
    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True, default='free')
    monthly_limit = models.IntegerField(default=500)

    def __str__(self):
        return f"{self.get_name_display()} - {self.monthly_limit} scans"

class WordpressShop(models.Model):
    # Identity
    domain = models.URLField(unique=True)
    admin_email = models.EmailField()
    api_key = models.CharField(max_length=64, unique=True)
    
    # Plan & Status
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Analytics & Quotas
    analysis_this_month = models.IntegerField(default=0)
    analysis_all_time = models.BigIntegerField(default=0)
    
    # Metadata for Debugging
    wp_version = models.CharField(max_length=10, blank=True)
    plugin_version = models.CharField(max_length=10, blank=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Automatically assign the 'Free' plan if no plan is set
        if not self.plan:
            free_plan, _ = Plan.objects.get_or_create(name='free', defaults={'monthly_limit': 500})
            self.plan = free_plan
        super().save(*args, **kwargs)

    @property
    def current_limit(self):
        return self.plan.monthly_limit if self.plan else 500

    def __str__(self):
        return self.domain
    

#clear cahce

@receiver([post_save, post_delete], sender=WordpressShop)
def clear_wordpress_cors_cache(sender, instance, **kwargs):
    """
    Clears the allowed origins cache whenever a WordPress shop is 
    created, updated (domain/active status change), or deleted.
    """
    cache.delete("allowed_origins")
    # A little logging helps with debugging later
    action = "modified" if kwargs.get('created', False) == False else "created/deleted"
    print(f"🧹 Wordpress CORS Cache cleared: {instance.domain} was {action}.")