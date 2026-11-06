from django.db import models
from users.models import CustomUser
from tasks.models import Task, TaskField


class Submission(models.Model):
    """Submission model for task submissions."""
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    worker = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='submissions')
    reviewed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')

    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    manager_feedback = models.TextField(blank=True)
    score = models.FloatField(null=True, blank=True, help_text='Score out of 100')
    progress = models.IntegerField(default=0, help_text='Progress percentage for this submission (0-100)')
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Submission for {self.task.title} by {self.worker.email}"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['task', 'worker', 'version']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['worker']),
            models.Index(fields=['submitted_at']),
        ]




class SubmissionComment(models.Model):
    """Comments on submissions for feedback and discussion."""
    
    ACTION_CHOICES = (
        ('comment', 'General Comment'),
        ('review_request', 'Changes Requested'),
        ('resubmission', 'Resubmission'),
        ('approval', 'Approval'),
    )
    
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    comment = models.TextField()
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES, default='comment')
    progress = models.IntegerField(null=True, blank=True, help_text='Progress at this point (0-100)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_action_type_display()} by {self.author.email} on {self.submission}"
    
    class Meta:
        ordering = ['-created_at']

class SubmissionFieldValue(models.Model):
    """Value for a custom task field in a submission."""
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='field_values')
    field = models.ForeignKey(TaskField, on_delete=models.CASCADE, related_name='submissions_values')
    value = models.TextField(blank=True, help_text='The value submitted for this custom field')
    file_upload = models.FileField(upload_to='submission_custom_files/', null=True, blank=True, help_text='Uploaded file for file field types')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['field__order', 'created_at']
        unique_together = ['submission', 'field']

    def __str__(self):
        return f"Value for {self.field.label} in {self.submission}"


class SubmissionVersion(models.Model):
    """Historical snapshot of a submission at a specific point in time."""
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()
    notes = models.TextField(blank=True)
    custom_fields_data = models.JSONField(default=dict, blank=True, help_text='Snapshot of TaskField values')
    progress = models.IntegerField(default=0)
    status = models.CharField(max_length=20, blank=True, null=True)
    score = models.FloatField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    snapshot_files = models.ManyToManyField('archives.Document', blank=True, related_name='version_snapshots')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = ['submission', 'version_number']

    def __str__(self):
        return f"Version {self.version_number} of {self.submission}"
