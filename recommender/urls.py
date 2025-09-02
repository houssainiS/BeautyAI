from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_photo, name='upload_photo'),  
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path("auth/callback/", views.oauth_callback, name="oauth_callback"),
    path("webhooks/app_uninstalled/", views.app_uninstalled, name="app_uninstalled"),
]
