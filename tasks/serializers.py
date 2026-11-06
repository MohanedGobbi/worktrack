from rest_framework import serializers
from tasks.models import Task
from users.serializers import CustomUserSerializer


class TaskSerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    assigned_to_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'created_by', 'created_by_email',
            'assigned_to', 'deadline', 'priority', 'estimated_hours', 'kpi_weight',
            'status', 'assigned_to_count', 'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_assigned_to_count(self, obj):
        return obj.assigned_to.count()
    
    def get_is_overdue(self, obj):
        return obj.is_overdue


class TaskDetailSerializer(TaskSerializer):
    created_by = CustomUserSerializer(read_only=True)
    assigned_to_list = CustomUserSerializer(source='assigned_to', many=True, read_only=True)
    
    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['assigned_to_list']


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    assigned_ids = serializers.PrimaryKeyRelatedField(
        queryset=__import__('users.models', fromlist=['CustomUser']).CustomUser.objects.all(),
        many=True,
        write_only=True,
        source='assigned_to'
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_ids',
            'deadline', 'priority', 'estimated_hours', 'kpi_weight', 'status', 'progress'
        ]
    
    def validate_deadline(self, value):
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("Deadline must be in the future.")
        return value
