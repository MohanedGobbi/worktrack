from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.contrib.auth import get_user_model
from users.serializers import CustomUserSerializer
from kpi.models import UserKPI
from kpi.serializers import UserKPISerializer
from tasks.models import Task
from submissions.models import Submission

User = get_user_model()


class DashboardViewSet(viewsets.ViewSet):
    """ViewSet for dashboard endpoints."""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def admin_dashboard(self, request):
        """Admin dashboard with global statistics."""
        if request.user.role != 'super_admin':
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Global statistics
        total_users = User.objects.count()
        total_tasks = Task.objects.filter(work_module__is_archived=False).count()
        total_submissions = Submission.objects.filter(task__work_module__is_archived=False).count()
        
        # Department performance
        departments = {}
        from users.models import Department
        for dept in Department.objects.all():
            dept_users = User.objects.filter(department=dept, role='worker')
            dept_kpi = UserKPI.objects.filter(user__in=dept_users)
            avg_score = dept_kpi.aggregate(Avg('total_score'))['total_score__avg'] or 0
            departments[dept.name] = avg_score
        
        # Task statistics
        task_by_status = Task.objects.filter(work_module__is_archived=False).values('status').annotate(count=Count('id'))
        
        # Top performers
        top_performers = UserKPI.objects.order_by('-total_score')[:5].values('user__email', 'total_score', 'month')
        
        return Response({
            'total_users': total_users,
            'total_tasks': total_tasks,
            'total_submissions': total_submissions,
            'departments': departments,
            'task_by_status': list(task_by_status),
            'top_performers': list(top_performers)
        })
    
    @action(detail=False, methods=['get'])
    def manager_dashboard(self, request):
        """Manager dashboard for team performance."""
        if request.user.role not in ['manager', 'super_admin']:
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from users.models import CustomUser
        team_users = CustomUser.objects.filter(department=request.user.department, role='worker')
        
        # Team statistics
        team_tasks = Task.objects.filter(assigned_to__in=team_users, work_module__is_archived=False).distinct()
        pending_submissions = Submission.objects.filter(
            task__in=team_tasks,
            status='submitted'
        ).count()
        
        # Team KPI
        team_kpi = UserKPI.objects.filter(user__in=team_users).order_by('-month')[:1]
        avg_score = team_kpi.aggregate(Avg('total_score'))['total_score__avg'] or 0
        
        return Response({
            'team_members': CustomUserSerializer(team_users, many=True).data,
            'total_tasks': team_tasks.count(),
            'pending_submissions': pending_submissions,
            'average_kpi_score': avg_score,
            'team_kpi': UserKPISerializer(team_kpi, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def worker_dashboard(self, request):
        """Worker dashboard with personal metrics."""
        # Worker statistics
        my_tasks = Task.objects.filter(assigned_to=request.user, work_module__is_archived=False)
        in_progress = my_tasks.filter(status='in_progress').count()
        completed = Submission.objects.filter(worker=request.user, status='approved', task__work_module__is_archived=False).count()
        pending_review = Submission.objects.filter(worker=request.user, status='submitted', task__work_module__is_archived=False).count()
        
        # My KPI
        my_kpi = UserKPI.objects.filter(user=request.user).order_by('-month')[:1]
        
        return Response({
            'my_tasks': my_tasks.count(),
            'in_progress': in_progress,
            'completed': completed,
            'pending_review': pending_review,
            'my_kpi': UserKPISerializer(my_kpi, many=True).data
        })
