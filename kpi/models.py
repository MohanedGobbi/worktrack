from django.db import models
from django.utils import timezone
from users.models import CustomUser
from datetime import datetime, timedelta


class KPIDefinition(models.Model):
    """Definition of KPI metrics."""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    weight = models.FloatField(default=1.0)
    formula = models.TextField(blank=True, help_text='Formula for calculation')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (Weight: {self.weight})"
    
    class Meta:
        ordering = ['name']


class UserKPI(models.Model):
    """User KPI records calculated monthly."""
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='kpi_records')
    month = models.DateField(help_text='First day of month')
    
    # KPI Metrics
    completion_rate = models.FloatField(default=0, help_text='Percentage of tasks completed')
    on_time_rate = models.FloatField(default=0, help_text='Percentage of tasks completed on time')
    quality_score = models.FloatField(default=0, help_text='Average quality score')
    rejection_rate = models.FloatField(default=0, help_text='Percentage of submissions rejected')
    productivity_score = models.FloatField(default=0, help_text='Tasks completed per month')
    
    # Final Score
    total_score = models.FloatField(default=0, help_text='Overall performance score')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    calculated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"KPI for {self.user.email} - {self.month.strftime('%B %Y')}"
    
    class Meta:
        ordering = ['-month']
        unique_together = ['user', 'month']
        indexes = [
            models.Index(fields=['user', 'month']),
            models.Index(fields=['month']),
        ]


class KPIWeight(models.Model):
    """Configurable weights for KPI calculation."""
    
    completion_rate_weight = models.FloatField(default=0.25)
    on_time_rate_weight = models.FloatField(default=0.25)
    quality_score_weight = models.FloatField(default=0.30)
    productivity_score_weight = models.FloatField(default=0.20)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return "KPI Weights Configuration"
    
    @classmethod
    def get_weights(cls):
        """Get current KPI weights."""
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance
    
    class Meta:
        verbose_name = "KPI Weight"
        verbose_name_plural = "KPI Weights"
