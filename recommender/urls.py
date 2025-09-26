from django.urls import path
from . import views , webhooks

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_photo, name='upload_photo'),  
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),

    path('app_entry/', views.app_entry, name='app_entry'),
    path('start_auth/', views.start_auth, name='start_auth'),
    path("auth/callback/", views.oauth_callback, name="oauth_callback"),
    path("webhooks/app_uninstalled/", webhooks.app_uninstalled, name="app_uninstalled"),
    path("create_page/", views.create_shopify_page, name="create_shopify_page"),
    path("documentation/", views.documentation, name="documentation"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("webhooks/order_updated/", webhooks.order_updated, name="order_updated_webhook"), 
]
