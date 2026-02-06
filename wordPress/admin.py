from django.contrib import admin
from .models import WordpressShop, Plan

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'monthly_limit')
    search_fields = ('name',)

@admin.register(WordpressShop)
class WordpressShopAdmin(admin.ModelAdmin):
    # 1. Columns for the list view
    # Note: 'plan' replaces 'plan_type', and 'current_limit' is a helper method below
    list_display = ('domain', 'plan', 'is_active', 'analysis_this_month', 'current_limit', 'created_at')
    
    # 2. Filters on the right sidebar
    list_filter = ('plan', 'is_active', 'created_at')
    
    # 3. Search functionality
    search_fields = ('domain', 'admin_email', 'api_key')
    
    # 4. Detailed View Organization (Fieldsets)
    fieldsets = (
        ('Site Identity', {
            'fields': ('domain', 'admin_email', 'api_key')
        }),
        ('Subscription Plan', {
            'fields': ('plan', 'is_active')
        }),
        ('Usage Statistics', {
            'description': "Track how many scans this shop has performed.",
            'fields': ('analysis_this_month', 'analysis_all_time')
        }),
        ('Technical & Metadata', {
            'classes': ('collapse',), # Collapsible section
            'fields': ('wp_version', 'plugin_version', 'last_heartbeat', 'created_at'),
        }),
    )
    
    # 5. Read-only fields to prevent accidental manual edits
    readonly_fields = ('api_key', 'analysis_all_time', 'last_heartbeat', 'created_at')

    # Helper method to show the numeric limit in the list view
    @admin.display(description='Scan Limit')
    def current_limit(self, obj):
        return obj.current_limit