from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze_domain, name='analyze_domain'),
    path('dashboard/', views.dashboard_view, name='dashboard_view'),
    path('dashboard/pairing-code/regenerate/', views.regenerate_pairing_code, name='regenerate_pairing_code'),
    path('dashboard/keywords/add/', views.add_blocked_keyword, name='add_blocked_keyword'),
    path('dashboard/keywords/<int:keyword_id>/delete/', views.delete_blocked_keyword, name='delete_blocked_keyword'),
    path('blocked-keywords/', views.get_blocked_keywords, name='get_blocked_keywords'),
    path('pairing-code/', views.create_pairing_code, name='create_pairing_code'),
    path('pair-device/', views.pair_child_device, name='pair_child_device'),
    path('device-location/', views.submit_device_location, name='submit_device_location'),
    path('site-visit/', views.report_site_visit, name='report_site_visit'),
]
