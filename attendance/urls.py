from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_dashboard, name='attendance-dashboard'),
    path('check-in/', views.check_in, name='attendance-check-in'),
    path('check-out/', views.check_out, name='attendance-check-out'),
    path('settings/', views.attendance_settings_view, name='attendance-settings'),
    path('export-csv/', views.export_attendance_xls, name='attendance-export-csv'),
]
