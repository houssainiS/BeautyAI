# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Shop, AllowedOrigin

# Trigger this function when a Shop or AllowedOrigin is saved or deleted
@receiver([post_save, post_delete], sender=Shop)
@receiver([post_save, post_delete], sender=AllowedOrigin)
def clear_cors_cache(sender, instance, **kwargs):
    """
    Clears the 'allowed_origins' cache whenever a Shop or AllowedOrigin 
    is modified. This ensures the middleware fetches fresh data immediately.
    """
    cache.delete("allowed_origins")
    print("🧹 Cache 'allowed_origins' cleared due to model update.")