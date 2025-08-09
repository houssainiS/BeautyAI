from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_photo, name='upload_photo'),  
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
]
