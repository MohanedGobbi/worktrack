from rest_framework import viewsets, permissions
from audit.models import ActivityLog


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for audit activity logs - read-only."""
    queryset = ActivityLog.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['user', 'action', 'object_type']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return ActivityLog.objects.all()
        else:
            # Users can see their own activities
            return ActivityLog.objects.filter(user=user)
