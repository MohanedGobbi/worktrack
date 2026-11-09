from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from submissions.models import Submission, SubmissionComment
from submissions.serializers import (
    SubmissionSerializer, SubmissionDetailSerializer, SubmissionCreateSerializer,
    SubmissionReviewSerializer, SubmissionCommentSerializer
)
from core.permissions import IsSubmissionOwner, IsManager
from audit.models import ActivityLog
from notifications.models import Notification
from core.email_notifications import notify_submission_received, notify_submission_reviewed


class SubmissionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing submissions."""
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['task', 'worker', 'status']
    ordering_fields = ['created_at', 'submitted_at']
    
    def get_permissions(self):
        # Staff create their own submissions; changing or deleting one afterwards (status, score, feedback) is a
        # reviewer's job, so a worker cannot approve or score their own work through the API.
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsManager()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubmissionDetailSerializer
        elif self.action == 'create':
            return SubmissionCreateSerializer
        elif self.action == 'review':
            return SubmissionReviewSerializer
        return SubmissionSerializer
    
    def get_queryset(self):
        user = self.request.user
        base_qs = Submission.objects.filter(Q(task__work_module__isnull=True) | Q(task__work_module__is_archived=False))
        if user.role == 'super_admin':
            return base_qs
        elif user.role == 'manager':
            return base_qs.filter(Q(task__created_by=user) | Q(worker=user))
        else:  # worker
            return base_qs.filter(worker=user)
    
    def perform_create(self, serializer):
        """Create submission as current user."""
        submission = serializer.save(worker=self.request.user, submitted_at=timezone.now())
        submission.status = 'submitted'
        submission.save()
        
        ActivityLog.objects.create(
            user=self.request.user,
            action='submit',
            object_type='Submission',
            object_id=submission.id,
            object_str=str(submission),
            description=f'Submission created for task: {submission.task.title}'
        )
        
        # Notify manager
        notify_submission_received(submission)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsManager])
    def review(self, request, pk=None):
        """Review submission (approve/reject/score)."""
        submission = self.get_object()
        
        # Allow review if user is the task creator OR if the user is a super_admin/manager
        # (IsManager permission already ensures the user has one of those roles)
        # The user's request specifically asked to allow admins to approve their own submissions.
        if submission.task.created_by != request.user and request.user.role not in ['super_admin', 'manager']:
            return Response(
                {"detail": "Only task creator or administrators can review"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SubmissionReviewSerializer(submission, data=request.data, partial=True)
        if serializer.is_valid():
            submission = serializer.save(reviewed_at=timezone.now())
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='review',
                object_type='Submission',
                object_id=submission.id,
                object_str=str(submission),
                description=f'Submission reviewed - Status: {submission.status}, Score: {submission.score}'
            )
            
            # Send notification to worker
            notify_submission_reviewed(submission)
            
            return Response(
                SubmissionSerializer(submission).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmissionCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for submission comments."""
    queryset = SubmissionComment.objects.all()
    serializer_class = SubmissionCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        submission_id = self.kwargs.get('submission_pk')
        base_qs = SubmissionComment.objects.filter(Q(submission__task__work_module__isnull=True) | Q(submission__task__work_module__is_archived=False))
        if submission_id:
            return base_qs.filter(submission_id=submission_id)
        return base_qs
    
    def perform_create(self, serializer):
        """Create comment as current user."""
        submission_id = self.kwargs.get('submission_pk')
        submission = Submission.objects.get(id=submission_id)
        serializer.save(author=self.request.user, submission=submission)
