from django.urls import path
from . import views , webhooks

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_photo, name='upload_photo'),  
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),

    path('start_auth/', views.start_auth, name='start_auth'),
    path("auth/callback/", views.oauth_callback, name="oauth_callback"),
    path("webhooks/app_uninstalled/", webhooks.app_uninstalled, name="app_uninstalled"),
    path("webhooks/app_uninstalled", webhooks.app_uninstalled),
]
