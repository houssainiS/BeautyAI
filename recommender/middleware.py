from .models import Visitor, AllowedOrigin, Shop
from wordPress.models import WordpressShop
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from django.conf import settings
from django.core.cache import cache

class VisitorTrackingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 1. Skip middleware for webhooks and OAuth callback
        if request.path.startswith("/webhooks/") or request.path.startswith("/auth/callback"):
            return 

        # 2. Cache CORS_ALLOWED_ORIGINS for 5 min instead of every request
        cors_urls = cache.get("allowed_origins")
        if cors_urls is None:
            try:
                # A. Fetch manually added origins
                allowed_from_model = list(AllowedOrigin.objects.values_list("url", flat=True))

                # B. Fetch active SHOPIFY shops (Standard + Custom domains)
                shop_domains = Shop.objects.filter(is_active=True).values_list("domain", "custom_domain")
                allowed_from_shops = []
                for domain, custom_domain in shop_domains:
                    if domain:
                        allowed_from_shops.append(f"https://{domain}")
                    if custom_domain:
                        allowed_from_shops.append(f"https://{custom_domain}")

                # C. Fetch active WORDPRESS Shops (With Protocol Safety)
                wp_domains = WordpressShop.objects.filter(is_active=True).values_list("domain", flat=True)
                allowed_from_wp = []
                for url in wp_domains:
                    if url:
                        # Clean whitespace and trailing slashes
                        clean_url = url.strip().rstrip('/')
                        # Ensure protocol exists; default to https if missing
                        if not clean_url.startswith(('http://', 'https://')):
                            clean_url = f"https://{clean_url}"
                        allowed_from_wp.append(clean_url)

                # D. Merge and deduplicate all
                cors_urls = list(set(allowed_from_model + allowed_from_shops + allowed_from_wp))
                cache.set("allowed_origins", cors_urls, 300)  # cache 5 min
            except Exception as e:
                print(f"Middleware Cache Error: {e}")
                cors_urls = []

        # Apply the merged origins to Django settings
        settings.CORS_ALLOWED_ORIGINS = cors_urls

        # 3. Only create session if needed (for visitor tracking)
        if not request.session.session_key and request.path.startswith("/analyze"):
            request.session.create()

        # 4. Log unique visitors per day
        if request.session.session_key:
            ip = self.get_client_ip(request)
            device_type = self.get_device_type(request)
            today = now().date()
            if not Visitor.objects.filter(session_key=request.session.session_key, date=today).exists():
                Visitor.objects.create(
                    session_key=request.session.session_key,
                    ip_address=ip,
                    device_type=device_type,
                    date=today
                )

    def process_response(self, request, response):
        """
        Add headers to allow Shopify embedded app in iframe.
        """
        if not request.path.startswith("/webhooks/"):
            # Allow embedding in Shopify admin
            response["X-Frame-Options"] = "ALLOWALL"
            
            # Content-Security-Policy focused on Shopify Admin
            response["Content-Security-Policy"] = (
                "frame-ancestors https://*.myshopify.com https://admin.shopify.com;"
            )
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")

    def get_device_type(self, request):
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        if "mobile" in user_agent:
            return "Mobile"
        elif "tablet" in user_agent:
            return "Tablet"
        return "Desktop"