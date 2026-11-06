# WorkTrack Pro - Developer Guide

Quick reference for common development tasks in WorkTrack Pro.

## Table of Contents
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Adding New Models](#adding-new-models)
- [Creating API Endpoints](#creating-api-endpoints)
- [Using Permissions](#using-permissions)
- [Working with KPIs](#working-with-kpis)
- [Database Queries](#database-queries)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Getting Started

### 1. Clone and Setup
```bash
git clone <repo>
cd worktrack_pro
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure Database
Edit `.env` and set your PostgreSQL credentials:
```env
DB_NAME=worktrack_pro
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
```

### 3. Initialize Database
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 4. Verify Setup
```bash
python verify_structure.py
curl http://localhost:8000/api/token/
```

## Project Structure

```
worktrack_pro/
├── users/              # User management, authentication
├── tasks/              # Task creation and assignment
├── submissions/        # Work submission and review
├── kpi/                # Performance metrics and calculations
├── notifications/      # Alerts and user preferences
├── audit/              # Activity logging and compliance
├── dashboards/         # Analytics and statistics
├── core/               # Shared utilities, permissions, middleware
└── worktrack_pro/      # Django project configuration
```

### Models Layer
- **Location**: `{app}/models.py`
- **Pattern**: Django ORM models with proper relationships
- **Example**: Task, Submission, UserKPI

### Serializers Layer
- **Location**: `{app}/serializers.py`
- **Pattern**: DRF serializers for validation and transformation
- **Usage**: Convert models to/from JSON

### Views Layer
- **Location**: `{app}/views.py`
- **Pattern**: DRF ViewSets for CRUD operations
- **Features**: Filtering, pagination, custom actions

### URLs Layer
- **Location**: `{app}/urls.py`
- **Pattern**: DefaultRouter with viewsets

## Adding New Models

### 1. Define Model in `{app}/models.py`
```python
from django.db import models
from users.models import CustomUser

class MyModel(models.Model):
    """Description of the model."""
    
    name = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']
```

### 2. Create Serializer in `{app}/serializers.py`
```python
from rest_framework import serializers
from myapp.models import MyModel

class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = ['id', 'name', 'user', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
```

### 3. Create ViewSet in `{app}/views.py`
```python
from rest_framework import viewsets, permissions
from myapp.models import MyModel
from myapp.serializers import MyModelSerializer

class MyModelViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    permission_classes = [permissions.IsAuthenticated]
```

### 4. Register in `{app}/urls.py`
```python
from rest_framework.routers import DefaultRouter
from myapp.views import MyModelViewSet

router = DefaultRouter()
router.register(r'mymodels', MyModelViewSet, basename='mymodel')

urlpatterns = [path('', include(router.urls))]
```

### 5. Register Admin in `{app}/admin.py`
```python
from django.contrib import admin
from myapp.models import MyModel

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name',)
```

### 6. Create Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## Creating API Endpoints

### Simple GET endpoint (uses ViewSet defaults)
```python
# automatically provides:
# GET /api/mymodels/
# GET /api/mymodels/{id}/
# POST /api/mymodels/
# PUT /api/mymodels/{id}/
```

### Custom Action (GET)
```python
class MyModelViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent items."""
        recent_items = MyModel.objects.all()[:10]
        serializer = MyModelSerializer(recent_items, many=True)
        return Response(serializer.data)
    
    # Endpoint: GET /api/mymodels/recent/
```

### Custom Action (POST with body)
```python
class TaskViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign task to workers."""
        task = self.get_object()
        worker_ids = request.data.get('worker_ids', [])
        workers = User.objects.filter(id__in=worker_ids)
        task.assigned_to.add(*workers)
        
        return Response(
            {"detail": f"Assigned to {workers.count()} workers"},
            status=status.HTTP_200_OK
        )
    
    # Endpoint: POST /api/tasks/{id}/assign/
    # Body: {"worker_ids": [1, 2, 3]}
```

## Using Permissions

### Check Role
```python
from core.permissions import IsSuperAdmin, IsManager, IsWorker

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsManager]
    
    # Only managers and super admins can access
```

### Check Object Ownership
```python
from core.permissions import IsTaskOwner

class TaskViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['put'], permission_classes=[IsTaskOwner])
    def update_task(self, request, pk=None):
        # Only task creator can update
        pass
```

### Custom Permission
```python
from rest_framework import permissions

class IsOwnSubmission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.worker == request.user or obj.task.created_by == request.user

class SubmissionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnSubmission]
```

## Working with KPIs

### Generate KPI for a User
```python
from kpi.engine import recalculate_user_kpi
from users.models import CustomUser

user = CustomUser.objects.get(id=1)
kpi = recalculate_user_kpi(user)
# kpi.total_score, kpi.completion_rate, etc.
```

### Generate All KPIs for a Month
```python
from kpi.engine import recalculate_all_kpis
from datetime import datetime

month = datetime(2026, 2, 1).date()
kpis = recalculate_all_kpis(month)
```

### Update KPI Weights
```python
from kpi.models import KPIWeight

weights = KPIWeight.get_weights()
weights.completion_rate_weight = 0.30
weights.on_time_rate_weight = 0.25
weights.quality_score_weight = 0.25
weights.productivity_score_weight = 0.20
weights.save()
```

### Get User's Current KPI
```python
from kpi.models import UserKPI
from django.utils import timezone

current_month = timezone.now().replace(day=1)
kpi = UserKPI.objects.filter(
    user=user,
    month=current_month
).first()

if kpi:
    print(f"Score: {kpi.total_score}")
```

## Database Queries

### Filter Operations
```python
from tasks.models import Task
from django.utils import timezone

# Basic filters
tasks = Task.objects.filter(status='pending')
tasks = Task.objects.filter(priority='high')

# Multiple conditions (AND)
tasks = Task.objects.filter(status='pending', priority='high')

# OR conditions
from django.db.models import Q
tasks = Task.objects.filter(Q(status='pending') | Q(status='in_progress'))

# NOT
tasks = Task.objects.exclude(status='completed')

# Datetime filtering
overdue = Task.objects.filter(deadline__lt=timezone.now())
recent = Task.objects.filter(created_at__gte=timezone.now() - timedelta(days=7))
```

### Aggregation
```python
from django.db.models import Count, Avg, Sum

# Count
task_count = Task.objects.count()
tasks_by_status = Task.objects.values('status').annotate(count=Count('id'))

# Average
avg_score = Submission.objects.aggregate(Avg('score'))['score__avg']

# Grouping
tasks_per_user = Task.objects.values('created_by').annotate(count=Count('id'))
```

### Relationships
```python
# Forward relation
task = Task.objects.get(id=1)
creator = task.created_by

# Reverse relation
user = CustomUser.objects.get(id=1)
my_tasks = user.created_tasks.all()

# ManyToMany
assigned_workers = task.assigned_to.all()
worker_tasks = worker.assigned_tasks.all()
```

### Select Related (Optimize Joins)
```python
# Without select_related: N+1 queries
tasks = Task.objects.all()
for task in tasks:
    print(task.created_by.email)  # Extra query per task

# With select_related: Single query
tasks = Task.objects.select_related('created_by')
for task in tasks:
    print(task.created_by.email)  # No extra queries
```

### Prefetch Related (Optimize M2M)
```python
# Without prefetch: N+1 queries
tasks = Task.objects.all()
for task in tasks:
    workers = task.assigned_to.all()  # Extra query per task

# With prefetch: Fewer queries
from django.db.models import Prefetch
tasks = Task.objects.prefetch_related('assigned_to')
for task in tasks:
    workers = task.assigned_to.all()  # No extra queries
```

## Testing

### Run All Tests
```bash
python manage.py test
```

### Run Tests for Specific App
```bash
python manage.py test users
```

### Run Specific Test Class
```bash
python manage.py test users.tests.CustomUserTestCase
```

### Run with Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # generates htmlcov/index.html
```

### Example Test
```python
from django.test import TestCase
from users.models import CustomUser

class CustomUserTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='worker'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'worker')
        self.assertTrue(self.user.is_active)
    
    def test_user_can_authenticate(self):
        from django.contrib.auth import authenticate
        auth_user = authenticate(email='test@example.com', password='testpass123')
        self.assertNotNone(auth_user)
```

## Troubleshooting

### Migration Issues
```bash
# Show migration status
python manage.py showmigrations

# Reset migrations (development only!)
python manage.py migrate {app} zero

# Create empty migration
python manage.py makemigrations {app} --empty {app} --name migration_name
```

### Database Connection Error
```bash
# Check PostgreSQL is running
psql -U postgres

# Test connection
python manage.py dbshell
```

### Import Errors
```bash
# Check PYTHONPATH
export PYTHONPATH=$PYTHONPATH:.

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -name "*.pyc" -delete
```

### Permission Denied Errors
```bash
# Check user role
python manage.py shell
>>> from users.models import CustomUser
>>> user = CustomUser.objects.get(email='user@example.com')
>>> user.role
'worker'
```

### Port Already in Use
```bash
# Use different port
python manage.py runserver 8001

# Or find and kill process
lsof -i :8000
kill -9 <PID>
```

## Common Patterns

### Signal Handler (Auto-trigger on model save)
```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser, UserProfile

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Now whenever a user is created, profile is auto-created
```

### Activity Logging
```python
from audit.models import ActivityLog

ActivityLog.objects.create(
    user=request.user,
    action='create',
    object_type='Task',
    object_id=task.id,
    object_str=task.title,
    description=f'Task created: {task.title}',
    ip_address=get_client_ip(request)
)
```

### Notifications
```python
from notifications.models import Notification

Notification.objects.create(
    recipient=user,
    notification_type='task_assigned',
    title='New Task Assigned',
    message=f'You have been assigned to: {task.title}',
    related_object_type='Task',
    related_object_id=task.id
)
```

---

**Last Updated**: February 2026
