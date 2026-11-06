from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notifications.views import (
    NotificationViewSet, 
    NotificationPreferenceViewSet,
    email_template_list,
    email_template_edit,
    email_preview,
    email_style_edit
)

app_name = 'notifications'

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'preferences', NotificationPreferenceViewSet, basename='notification-preference')

urlpatterns = [
    path('api/', include(router.urls)),
    path('manage/', email_template_list, name='email-list'),
    path('manage/<int:template_id>/edit/', email_template_edit, name='email-edit'),
    path('manage/<int:template_id>/preview/', email_preview, name='email-preview'),
    path('manage/style/', email_style_edit, name='email-style-edit'),
]
