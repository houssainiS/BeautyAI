from django.urls import path
from . import views

from django.http import HttpResponse

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_photo, name='upload_photo'),
    path('health/', lambda request: HttpResponse('ok')),
]
