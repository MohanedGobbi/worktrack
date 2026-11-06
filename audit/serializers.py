from rest_framework import serializers
from audit.models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_email', 'action', 'object_type',
            'object_id', 'object_str', 'description', 'changes',
            'ip_address', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'action', 'object_type', 'object_id',
            'object_str', 'description', 'changes', 'ip_address', 'created_at'
        ]
