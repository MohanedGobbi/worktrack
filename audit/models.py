from django.db import models
from django.contrib.contenttypes.models import ContentType
from users.models import CustomUser


class ActivityLog(models.Model):
    """Audit log for tracking all system activities."""
    
    ACTION_TYPES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('assign', 'Assign'),
        ('submit', 'Submit'),
        ('review', 'Review'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    object_type = models.CharField(max_length=100)
    object_id = models.IntegerField()
    object_str = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.action.upper()} {self.object_type} - {self.object_str}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
