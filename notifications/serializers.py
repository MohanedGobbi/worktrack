from rest_framework import serializers
from notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    recipient_email = serializers.CharField(source='recipient.email', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_email', 'notification_type', 'title',
            'message', 'related_object_type', 'related_object_id', 'is_read',
            'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'recipient', 'created_at', 'read_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'user', 'user_email', 'email_on_task_assigned',
            'email_on_submission_received', 'email_on_deadline_reminder',
            'email_on_kpi_updated', 'in_app_notifications',
            'reminder_days_before_deadline'
        ]
        read_only_fields = ['user']
