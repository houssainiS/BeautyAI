from .models import Visitor, AllowedOrigin
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from django.conf import settings

class VisitorTrackingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 🔹 Update CORS_ALLOWED_ORIGINS dynamically from DB
        try:
            settings.CORS_ALLOWED_ORIGINS = list(
                AllowedOrigin.objects.values_list("url", flat=True)
            )
        except Exception:
            pass

        # 🔹 Existing visitor tracking logic
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        ip = self.get_client_ip(request)
        device_type = self.get_device_type(request)

        # Log unique visitors per day
        today = now().date()
        if not Visitor.objects.filter(session_key=session_key, date=today).exists():
            Visitor.objects.create(
                session_key=session_key,
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
