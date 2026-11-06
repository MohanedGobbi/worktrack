from django.db import models
from django.conf import settings
import os

class Document(models.Model):
    """
    Centralized document tracking system.
    Stores all files uploaded to the system with their context.
    """
    TYPE_CHOICES = (
        ('task_attachment', 'Task Attachment'),
        ('submission_file', 'Submission File'),
        ('submission_comment_file', 'Submission Comment Attachment'),
        ('task_comment_file', 'Task Comment Attachment'),
        ('general', 'General / Internal'),
    )

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='general')
    version = models.IntegerField(default=1, help_text='Tracks which submission version this file belongs to')
    
    # Context links
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    submission_comment = models.ForeignKey('submissions.SubmissionComment', on_delete=models.CASCADE, null=True, blank=True, related_name='attached_documents')
    task_comment = models.ForeignKey('tasks.TaskComment', on_delete=models.CASCADE, null=True, blank=True, related_name='attached_documents')
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_documents')
    
    # Metadata
    file_size = models.BigIntegerField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.title or self.file.name

    @property
    def filename(self):
        """Get original or clean base filename."""
        if self.original_filename:
            return self.original_filename
        if self.file and self.file.name:
            return self.file.name.split('/')[-1]
        return self.title or 'Attachment'

    @property
    def display_size(self):
        """Safely get file size even if file is missing from storage."""
        if self.file_size:
            return self.file_size
        try:
            if self.file and self.file.storage.exists(self.file.name):
                return self.file.size
        except (OSError, ValueError, FileNotFoundError):
            pass
        return 0

    def save(self, *args, **kwargs):
        """Auto-populate original_filename, sanitize filename, and set file_size on save."""
        from core.utils import sanitize_filename

        if self.file and not self.original_filename:
            self.original_filename = os.path.basename(self.file.name)

        if self.file and self.file.name:
            clean_name = sanitize_filename(self.file.name)
            if self.file.name != clean_name:
                self.file.name = clean_name

        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except (OSError, ValueError, FileNotFoundError):
                pass
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-uploaded_at']
