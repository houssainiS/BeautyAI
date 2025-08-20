from django.urls import path
from . import views

urlpatterns = [
    path('webhook/install/', views.install_webhook, name='shopify_install_webhook'),
    path('oauth/start/', views.start_oauth, name='shopify_oauth_start'),
    path('oauth/callback/', views.oauth_callback, name='shopify_oauth_callback'),
]
