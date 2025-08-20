from django.contrib import admin
from .models import Shop
# Register your models here.
@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('shop_domain', 'installed_at', 'active')
    search_fields = ('shop_domain',)