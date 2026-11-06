from rest_framework import serializers
from submissions.models import Submission, SubmissionComment
from users.serializers import CustomUserSerializer
from tasks.serializers import TaskSerializer


class SubmissionCommentSerializer(serializers.ModelSerializer):
    author_email = serializers.CharField(source='author.email', read_only=True)
    
    class Meta:
        model = SubmissionComment
        fields = ['id', 'author', 'author_email', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class SubmissionSerializer(serializers.ModelSerializer):
    worker_email = serializers.CharField(source='worker.email', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    comments = SubmissionCommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id', 'task', 'task_title', 'worker', 'worker_email',
            'notes', 'status', 'submitted_at', 'reviewed_at', 'manager_feedback',
            'score', 'version', 'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'worker', 'submitted_at', 'reviewed_at', 'version', 'created_at', 'updated_at']


class SubmissionDetailSerializer(SubmissionSerializer):
    worker = CustomUserSerializer(read_only=True)
    task = TaskSerializer(read_only=True)
    
    class Meta(SubmissionSerializer.Meta):
        pass


class SubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['task', 'notes', 'status']
    
    def validate_task(self, value):
        from django.utils import timezone
        if value.deadline < timezone.now():
            raise serializers.ValidationError("Cannot submit for overdue task.")
        return value


class SubmissionReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['status', 'manager_feedback', 'score']
    
    def validate_score(self, value):
        if value is not None and not (0 <= value <= 100):
            raise serializers.ValidationError("Score must be between 0 and 100.")
        return value
