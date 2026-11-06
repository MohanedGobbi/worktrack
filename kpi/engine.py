"""
KPI Calculation Engine

Handles automatic KPI calculation for users based on their task performance,
submissions, and other metrics.
"""

from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg, F, Case, When
from kpi.models import UserKPI, KPIWeight
from tasks.models import Task
from submissions.models import Submission
from users.models import CustomUser


class KPICalculationEngine:
    """Main engine for calculating user KPIs."""
    
    def __init__(self, user, month=None):
        self.user = user
        if month is None:
            month = timezone.now().replace(day=1)
        self.month = month
        self.weights = KPIWeight.get_weights()
    
    def calculate_completion_rate(self):
        """Calculate task completion rate for the month."""
        total_assigned = Task.objects.filter(
            assigned_to=self.user,
            created_at__month=self.month.month,
            created_at__year=self.month.year
        ).count()
        
        if total_assigned == 0:
            return 0
        
        completed = Submission.objects.filter(
            worker=self.user,
            status__in=['approved', 'submitted'],
            submitted_at__month=self.month.month,
            submitted_at__year=self.month.year
        ).count()
        
        return (completed / total_assigned) * 100
    
    def calculate_on_time_rate(self):
        """Calculate on-time delivery rate for the month."""
        total_submitted = Submission.objects.filter(
            worker=self.user,
            submitted_at__isnull=False,
            submitted_at__month=self.month.month,
            submitted_at__year=self.month.year
        ).count()
        
        if total_submitted == 0:
            return 0
        
        on_time = Submission.objects.filter(
            worker=self.user,
            submitted_at__isnull=False,
            submitted_at__lte=F('task__deadline'),
            submitted_at__month=self.month.month,
            submitted_at__year=self.month.year
        ).count()
        
        return (on_time / total_submitted) * 100
    
    def calculate_quality_score(self):
        """Calculate average quality score from submission scores."""
        submissions = Submission.objects.filter(
            worker=self.user,
            score__isnull=False,
            reviewed_at__month=self.month.month,
            reviewed_at__year=self.month.year
        )
        
        if not submissions.exists():
            return 0
        
        return submissions.aggregate(avg_score=Avg('score'))['avg_score'] or 0
    
    def calculate_rejection_rate(self):
        """Calculate rejection rate."""
        total_reviewed = Submission.objects.filter(
            worker=self.user,
            reviewed_at__isnull=False,
            reviewed_at__month=self.month.month,
            reviewed_at__year=self.month.year
        ).count()
        
        if total_reviewed == 0:
            return 0
        
        rejected = Submission.objects.filter(
            worker=self.user,
            status='rejected',
            reviewed_at__month=self.month.month,
            reviewed_at__year=self.month.year
        ).count()
        
        return (rejected / total_reviewed) * 100
    
    def calculate_productivity_score(self):
        """Calculate productivity score based on completed tasks."""
        completed_tasks = Submission.objects.filter(
            worker=self.user,
            status='approved',
            submitted_at__month=self.month.month,
            submitted_at__year=self.month.year
        ).count()
        
        # Normalize to 100 (assume 10 tasks per month is full productivity)
        return min((completed_tasks / 10) * 100, 100)
    
    def calculate_total_score(self):
        """Calculate weighted total KPI score."""
        completion_rate = self.calculate_completion_rate()
        on_time_rate = self.calculate_on_time_rate()
        quality_score = self.calculate_quality_score()
        productivity_score = self.calculate_productivity_score()
        
        total_score = (
            (completion_rate * self.weights.completion_rate_weight) +
            (on_time_rate * self.weights.on_time_rate_weight) +
            (quality_score * self.weights.quality_score_weight) +
            (productivity_score * self.weights.productivity_score_weight)
        )
        
        return min(total_score, 100)  # Cap at 100
    
    def calculate_and_save(self):
        """Calculate all KPIs and save to database."""
        kpi, created = UserKPI.objects.get_or_create(
            user=self.user,
            month=self.month
        )
        
        kpi.completion_rate = self.calculate_completion_rate()
        kpi.on_time_rate = self.calculate_on_time_rate()
        kpi.quality_score = self.calculate_quality_score()
        kpi.rejection_rate = self.calculate_rejection_rate()
        kpi.productivity_score = self.calculate_productivity_score()
        kpi.total_score = self.calculate_total_score()
        kpi.save()
        
        return kpi


def recalculate_user_kpi(user, month=None):
    """Convenience function to recalculate a user's KPI."""
    engine = KPICalculationEngine(user, month)
    return engine.calculate_and_save()


def recalculate_all_kpis(month=None):
    """Recalculate KPIs for all active users."""
    users = CustomUser.objects.filter(is_active=True)
    results = []
    for user in users:
        kpi = recalculate_user_kpi(user, month)
        results.append(kpi)
    return results
