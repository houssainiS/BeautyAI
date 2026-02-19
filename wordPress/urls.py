from django.urls import path
from . import views

urlpatterns = [
    path('connect/', views.connect_page, name='wp-connect'),
    path('finalize/', views.finalize_connection, name='wp-finalize'),
    path('deactivate/', views.deactivate_shop, name='wp-deactivate'),
    path('analyze/', views.wp_analyze_photo, name='wp-analyze'),
    path('status/', views.wp_shop_status, name='wp-status'),
]