from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Visitor, FaceAnalysis , Feedback , AllowedOrigin ,Shop , PageContent ,Purchase

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'device_type', 'date')
    list_filter = ('device_type', 'date')
    search_fields = ('ip_address',)


@admin.register(FaceAnalysis)
class FaceAnalysisAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'device_type', 'timestamp')
    list_filter = ('device_type', 'timestamp')
    search_fields = ('ip_address',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('feedback_type', 'dislike_reason', 'created_at')
    list_filter = ('feedback_type', 'created_at')
    search_fields = ('dislike_reason',)
    readonly_fields = ('created_at',)

# Change admin site headers and titles
admin.site.site_header = "Webixia"
admin.site.site_title = "Webixia"
admin.site.index_title = "Welcome to Skin Analyzer Dashboard"

# Remove Groups from admin
admin.site.unregister(Group)

#shopify urls table
@admin.register(AllowedOrigin)
class AllowedOriginAdmin(admin.ModelAdmin):
    list_display = ("url", "created_at")
    search_fields = ("url",)



###webhooks#####

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('domain', 'installed_at', 'is_active')
    search_fields = ("domain",)


@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at')  # show these columns in admin list
    ordering = ('-updated_at',)  # newest first


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "product_name",
        "purchase_date",
        "usage_duration_days",
        "notified",
        "expiry_date",
    )
    list_filter = ("notified", "purchase_date")
    search_fields = ("email", "product_name", "order_id")
    readonly_fields = ("expiry_date",)