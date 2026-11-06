from django.db import models
from users.models import CustomUser


class Notification(models.Model):
    """Notification model for in-app and email notifications."""
    
    NOTIFICATION_TYPES = (
        ('task_assigned', 'Task Assigned'),
        ('task_created', 'Task Created'),
        ('correspondence_issued', 'Correspondence Issued'),
        ('submission_received', 'Submission Received'),
        ('submission_approved', 'Submission Approved'),
        ('submission_rejected', 'Submission Rejected'),
        ('deadline_reminder', 'Deadline Reminder'),
        ('kpi_updated', 'KPI Updated'),
        ('feedback_received', 'Feedback Received'),
    )
    
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} to {self.recipient.email}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['-created_at']),
        ]


class NotificationPreference(models.Model):
    """User notification preferences."""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='notification_preference')
    email_on_task_assigned = models.BooleanField(default=True)
    email_on_submission_received = models.BooleanField(default=True)
    email_on_deadline_reminder = models.BooleanField(default=True)
    email_on_kpi_updated = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    reminder_days_before_deadline = models.IntegerField(default=1)
    
    def __str__(self):
        return f"Notification preferences for {self.user.email}"
    
    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"


class EmailTemplate(models.Model):
    """Customizable email templates for different notification types."""
    notification_type = models.CharField(max_length=50, choices=Notification.NOTIFICATION_TYPES, unique=True)
    subject = models.CharField(max_length=255)
    body = models.TextField(help_text="HTML/Text body. Use placeholders like {task_title}, {worker_name}, etc.")
    is_html = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Template for {self.get_notification_type_display()}"


class EmailStyle(models.Model):
    """Global styling for system emails."""
    company_name = models.CharField(max_length=255, default="WorkTrack Pro")
    primary_color = models.CharField(max_length=7, default="#2563eb", help_text="Hex color code (e.g., #2563eb)")
    secondary_color = models.CharField(max_length=7, default="#10b981", help_text="Hex color code (e.g., #10b981)")
    logo_url = models.URLField(blank=True, null=True, help_text="URL to company logo image")
    footer_text = models.TextField(blank=True, default="© 2026 WorkTrack Pro. All rights reserved.")
    
    def __str__(self):
        return "Global Email Style"

    class Meta:
        verbose_name = "Email Style"
        verbose_name_plural = "Email Styles"
