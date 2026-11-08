from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from tasks.models import Task
from tasks.serializers import TaskSerializer, TaskDetailSerializer, TaskCreateUpdateSerializer
from core.permissions import IsManager, IsTaskOwner, IsTaskAssignee
from audit.models import ActivityLog


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tasks."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'deadline', 'priority']
    filterset_fields = ['status', 'priority']
    
    def get_permissions(self):
        # Staff read what is assigned to them; creating, changing and deleting tasks is for managers and administrators.
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsManager()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TaskDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskSerializer
    
    def get_queryset(self):
        user = self.request.user
        base_qs = Task.objects.filter(work_module__is_archived=False)
        if user.role == 'super_admin':
            return base_qs
        elif user.role == 'manager':
            return base_qs.filter(Q(created_by=user) | Q(assigned_to=user))
        else:  # worker
            return base_qs.filter(assigned_to=user)
    
    def perform_create(self, serializer):
        """Create task and assign creator."""
        task = serializer.save(created_by=self.request.user)
        ActivityLog.objects.create(
            user=self.request.user,
            action='create',
            object_type='Task',
            object_id=task.id,
            object_str=task.title,
            description=f'Task created: {task.title}',
            ip_address=self.request.client_ip if hasattr(self.request, 'client_ip') else None
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsManager])
    def assign(self, request, pk=None):
        """Assign task to workers."""
        task = self.get_object()
        if task.created_by != request.user:
            return Response(
                {"detail": "Only task creator can assign"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        worker_ids = request.data.get('worker_ids', [])
        workers = CustomUser.objects.filter(id__in=worker_ids, role='worker')
        task.assigned_to.add(*workers)
        
        ActivityLog.objects.create(
            user=request.user,
            action='assign',
            object_type='Task',
            object_id=task.id,
            object_str=task.title,
            description=f'Task assigned to {len(workers)} worker(s)'
        )
        
        return Response(
            {"detail": f"Task assigned to {len(workers)} worker(s)"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Mark task as in progress."""
        task = self.get_object()
        if request.user not in task.assigned_to.all():
            return Response(
                {"detail": "Not assigned to this task"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        task.status = 'in_progress'
        task.save()
        
        ActivityLog.objects.create(
            user=request.user,
            action='update',
            object_type='Task',
            object_id=task.id,
            object_str=task.title,
            description=f'Task status changed to in_progress'
        )
        
        return Response(
            TaskSerializer(task).data,
            status=status.HTTP_200_OK
        )


# Import CustomUser here to avoid circular imports
from users.models import CustomUser
