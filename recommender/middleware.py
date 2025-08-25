from .models import Visitor, AllowedOrigin
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from django.conf import settings
from django.core.cache import cache

class VisitorTrackingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # ✅ Cache CORS_ALLOWED_ORIGINS for 5 min instead of every request
        cors_urls = cache.get("allowed_origins")
        if cors_urls is None:
            try:
                cors_urls = list(AllowedOrigin.objects.values_list("url", flat=True))
                cache.set("allowed_origins", cors_urls, 300)  # cache 5 min
            except Exception:
                cors_urls = []
        settings.CORS_ALLOWED_ORIGINS = cors_urls

        # ✅ Only create session if needed
        if not request.session.session_key and request.path.startswith("/analyze"):
            request.session.create()

        # ✅ Log unique visitors per day (optional: throttle/batch this)
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

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def get_device_type(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'mobile' in user_agent:
            return 'Mobile'
        elif 'tablet' in user_agent:
            return 'Tablet'
        return 'Desktop'
