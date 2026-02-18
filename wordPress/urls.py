from django.urls import path, re_path # Import re_path
from . import views

urlpatterns = [
    path('connect/', views.connect_page, name='wp-connect'),
    path('finalize/', views.finalize_connection, name='wp-finalize'),
    path('deactivate/', views.deactivate_shop, name='wp-deactivate'),
    path('analyze/', views.wp_analyze_photo, name='wp-analyze'),
    path('status/', views.wp_shop_status, name='wp-status'),
    
    # Change 'path' to 're_path' to make the slash optional
    re_path(r'^uninstall/?$', views.wp_uninstall_webhook, name='wp_uninstall_webhook'),
]