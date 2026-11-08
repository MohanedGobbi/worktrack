from django.db import models
from django.utils import timezone
from users.models import CustomUser
from work_modules.models import WorkModule


class Tag(models.Model):
    """Tags for task categorization."""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#667eea', help_text='Hex color code (e.g., #667eea)')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


import io
import os
import subprocess
try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files import File

class Task(models.Model):
    """Task model for work assignments."""
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    )
    

    TASK_TYPE_CHOICES = (
        ('standard', 'Standard Task'),
        ('correspondence', 'Administrative Correspondence'),
    )

    CORRESPONDENCE_TYPE_CHOICES = (
        ('circular', 'Circular'),
        ('directive', 'Directive'),
        ('memo', 'Memo'),
        ('notice', 'Notice'),
        ('decision', 'Decision'),
    )
    
    work_module = models.ForeignKey(WorkModule, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')

    # Task type — standard work vs. administrative correspondence
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='standard')
    correspondence_type = models.CharField(max_length=20, choices=CORRESPONDENCE_TYPE_CHOICES, null=True, blank=True)
    reference_number = models.CharField(max_length=100, null=True, blank=True, help_text='Official reference number for the correspondence')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ManyToManyField(CustomUser, related_name='assigned_tasks')
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateTimeField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    estimated_hours = models.FloatField(default=0)
    kpi_weight = models.FloatField(default=1.0, help_text='Weight for KPI calculation')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0, help_text='Collective progress percentage (0-100)')
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    cover_image = models.ImageField(upload_to='task_covers/', blank=True, null=True, help_text='Optional cover image for the task widget')
    attachment = models.FileField(upload_to='task_attachments/', blank=True, null=True, help_text='Primary attachment (e.g., PDF for correspondence)')

    @property
    def attachment_filename(self):
        """Get base filename of primary attachment."""
        if self.attachment and self.attachment.name:
            return self.attachment.name.split('/')[-1]
        return ""
    
    RECURRENCE_CHOICES = (
        ('daily', 'Every Day'),
        ('weekly', 'Every Week'),
        ('monthly', 'Every Month'),
        ('quarterly', 'Every 3 Months'),
        ('yearly', 'Every Year'),
    )

    RECURRENCE_TYPE_CHOICES = (
        ('preset', 'Preset Interval'),
        ('custom', 'Custom Interval'),
    )

    RECURRENCE_UNIT_CHOICES = (
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
    )

    is_recurring = models.BooleanField(default=False)
    recurrence_type = models.CharField(max_length=20, choices=RECURRENCE_TYPE_CHOICES, default='preset')
    recurrence_interval = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, null=True, blank=True)
    
    # Custom recurrence fields
    recurrence_value = models.IntegerField(null=True, blank=True, help_text='Value for custom recurrence')
    recurrence_unit = models.CharField(max_length=20, choices=RECURRENCE_UNIT_CHOICES, null=True, blank=True)
    
    recurrence_limit = models.IntegerField(default=-1, help_text='-1 for forever, or a specific number of times')
    
    last_reactivated_at = models.DateTimeField(null=True, blank=True, help_text='Tracks the start of the current recurrence cycle')
    
    # Timeline ordering properties
    is_timeline_task = models.BooleanField(default=False, help_text="If true, this task plays a part in a configured sequence timeline.")
    sequence_order = models.IntegerField(null=True, blank=True, help_text="Order within the module's timeline.")
    
    # Location features
    location_enabled = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    wilaya = models.CharField(max_length=100, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        return timezone.now() > self.deadline and self.status not in ['approved', 'rejected']
    
    @property
    def timeline_progress(self):
        """Calculate percentage of time elapsed from start_date (or created_at) to deadline."""
        start_val = self.start_date or self.created_at
        if not start_val or not self.deadline:
            return 0
            
        from django.utils import timezone
        import datetime
        now = timezone.now()
        
        if isinstance(start_val, datetime.datetime):
            start = start_val
        else:
            start = timezone.make_aware(datetime.datetime.combine(start_val, datetime.time.min))
            
        if now <= start:
            return 0
        if now >= self.deadline:
            return 100
            
        total_duration = (self.deadline - start).total_seconds()
        elapsed = (now - start).total_seconds()
        
        if total_duration <= 0:
            return 100
            
        percentage = int((elapsed / total_duration) * 100)
        return min(max(percentage, 0), 100)

    @property
    def team_members(self):
        """Returns all assigned users for template compatibility."""
        return self.assigned_to.all()

    @property
    def recurrence_display(self):
        """Returns a human-readable display string for the recurrence interval."""
        if not self.is_recurring:
            return "None"
        
        if self.recurrence_type == 'preset':
            return self.get_recurrence_interval_display()
        
        if self.recurrence_value and self.recurrence_unit:
            unit = self.recurrence_unit
            if self.recurrence_value == 1:
                # Singularize unit if value is 1
                if unit.endswith('s'):
                    unit = unit[:-1]
            return f"Every {self.recurrence_value} {unit.capitalize()}"
        
        return "Custom"

    def get_recurrence_delta(self):
        """Helper to get relativedelta based on recurrence settings."""
        from dateutil.relativedelta import relativedelta
        if self.recurrence_type == 'preset':
            if self.recurrence_interval == 'daily':
                return relativedelta(days=1)
            elif self.recurrence_interval == 'weekly':
                return relativedelta(weeks=1)
            elif self.recurrence_interval == 'monthly':
                return relativedelta(months=1)
            elif self.recurrence_interval == 'quarterly':
                return relativedelta(months=3)
            elif self.recurrence_interval == 'yearly':
                return relativedelta(years=1)
        elif self.recurrence_type == 'custom' and self.recurrence_value and self.recurrence_unit:
            kwargs = {self.recurrence_unit: self.recurrence_value}
            return relativedelta(**kwargs)
        return None

    @property
    def next_reactivation_date(self):
        """Calculate the next expected reactivation date."""
        if not self.is_recurring or not self.deadline:
            return None
        
        delta = self.get_recurrence_delta()
        if not delta:
            return None

        now = timezone.now()
        next_date = self.deadline
        # Find the next reactivation in the future
        while next_date <= now:
            next_date += delta
            
        return next_date

    def reactivate_if_needed(self, force=False):
        """
        Check if the task's deadline has passed and reactivate it for a new cycle.
        If force=True, reactivate immediately.
        """
        if not self.is_recurring:
            return False
            
        now = timezone.now()
        # If not forcing, check if deadline has passed
        if not force and (not self.deadline or self.deadline > now):
            return False
            
        delta = self.get_recurrence_delta()
        if not delta:
            return False
            
        old_deadline = self.deadline
        new_deadline = old_deadline
        cycles_skipped = 0
        
        # Calculate how many cycles to move forward
        # If it's a 'force', we move at least one cycle
        if force:
            new_deadline += delta
            cycles_skipped = 1
            
        # If it's past due, catch up to the current/future cycle
        while new_deadline <= now:
            new_deadline += delta
            cycles_skipped += 1
            
        # Check recurrence limit
        if self.recurrence_limit != -1:
            if self.recurrence_limit <= cycles_skipped:
                # Limit reached or exceeded
                self.recurrence_limit = 0
                self.is_recurring = False
            else:
                self.recurrence_limit -= cycles_skipped
                
        # Update start date if it exists
        if self.start_date:
            from dateutil.relativedelta import relativedelta
            days_diff = (new_deadline - old_deadline).days
            self.start_date = self.start_date + relativedelta(days=days_diff)
            
        # Reset task state for the new cycle
        self.deadline = new_deadline
        self.status = 'pending'
        self.progress = 0
        self.last_reactivated_at = now
        self.save()
        
        # Log reactivation
        try:
            from audit.models import ActivityLog
            ActivityLog.objects.create(
                user=self.created_by,
                action='update',
                object_type='Task',
                object_id=self.id,
                object_str=self.title,
                description=f'Task reactivated for new cycle. Missed cycles: {cycles_skipped}. Next deadline: {self.deadline}.'
            )
        except:
            pass
            
        return True

    def recalculate_progress(self):
        """Recalculate progress based on average of latest submissions from all assigned users."""
        all_assigned = self.assigned_to.all()
        total_assigned = all_assigned.count()
        
        if total_assigned > 0:
            total_progress = 0
            approved_workers = 0
            
            for user in all_assigned:
                # Get the latest submission for this user (including drafts/submitted/approved)
                latest_sub = self.submissions.filter(worker=user)
                if self.is_recurring and self.last_reactivated_at:
                    latest_sub = latest_sub.filter(created_at__gte=self.last_reactivated_at)
                
                latest_sub = latest_sub.order_by('-created_at').first()
                
                if latest_sub:
                    total_progress += latest_sub.progress
                    if latest_sub.status == 'approved':
                        approved_workers += 1
            
            # Average progress across all assigned users
            self.progress = int(total_progress / total_assigned)
            
            # Update status logic: 
            if approved_workers == total_assigned:
                self.status = 'completed'
            else:
                # If it's not completed, check if it should be rejected or submitted
                # We check the latest relevant submissions from all assigned users
                worker_statuses = []
                for user in all_assigned:
                    sub = self.submissions.filter(worker=user).order_by('-created_at').first()
                    if sub:
                        worker_statuses.append(sub.status)
                    else:
                        worker_statuses.append('pending')
                
                if 'rejected' in worker_statuses:
                    self.status = 'rejected'
                elif all(s in ['approved', 'submitted'] for s in worker_statuses if s != 'pending') and any(s == 'submitted' for s in worker_statuses):
                    # Transition to submitted only if no one is rejected and at least one is submitted
                    # This logic might need refinement for multi-worker tasks
                    self.status = 'submitted'
                elif self.progress > 0 or any(s != 'pending' for s in worker_statuses):
                    self.status = 'in_progress'
                else:
                    self.status = 'pending'
        else:
            # No users assigned, progress remains as is or 0
            pass
            
        self.save()
        return self.progress

    def generate_cover_from_attachment(self):
        """Autogenerate a cover image from the primary attachment if it's a PDF."""
        if not convert_from_path:
            return
        if self.task_type == 'correspondence' and self.attachment and not self.cover_image:
            filename = self.attachment.name.lower()
            if filename.endswith('.pdf'):
                try:
                    # Extract the first page of the PDF
                    pages = convert_from_path(self.attachment.path, first_page=1, last_page=1, size=800)
                    if pages:
                        image = pages[0]
                        
                        # Save image to a BytesIO object
                        image_io = io.BytesIO()
                        image.save(image_io, format='JPEG', quality=85)
                        image_io.seek(0)
                        
                        # Use the original filename to create a cover image name
                        base_name = self.attachment.name.split('/')[-1].rsplit('.', 1)[0]
                        cover_name = f"{base_name}_cover.jpg"
                        
                        # Save the ContentFile to the cover_image field (doesn't trigger DB save)
                        self.cover_image.save(cover_name, ContentFile(image_io.read()), save=False)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to generate cover image for Task {self.id}: {str(e)}")

    def save(self, *args, **kwargs):
        # We need to save first if the attachment is new, so `attachment.path` exists on disk.
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # After initial save, if it's a correspondence task and missing a cover image,
        # but has an attachment, try to generate it.
        if self.task_type == 'correspondence' and self.attachment and not self.cover_image:
            self.generate_cover_from_attachment()
            # Save again to commit the cover image field update
            if self.cover_image:
                super().save(update_fields=['cover_image'])

    @property
    def detail_url(self):
        """Returns direct correspondence-detail URL if task_type is correspondence, otherwise task-detail."""
        if self.task_type == 'correspondence':
            from django.urls import reverse
            corr = Correspondence.objects.filter(
                models.Q(reference_number=self.reference_number, reference_number__isnull=False) |
                models.Q(title=self.title)
            ).first()
            if corr:
                return reverse('correspondence-detail', kwargs={'pk': corr.pk})
        from django.urls import reverse
        return reverse('task-detail', kwargs={'task_id': self.id})

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['deadline']),
            models.Index(fields=['created_by']),
        ]




class TaskComment(models.Model):
    """Discussion thread comment on a task.

    Allows workers and managers to communicate about a task
    without creating a full submission.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='task_comments')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        """Sanitize attachment and cover_image filenames on save if present."""
        from core.utils import sanitize_filename

        if hasattr(self, 'attachment') and self.attachment and getattr(self.attachment, 'name', None):
            clean_att = sanitize_filename(self.attachment.name)
            if self.attachment.name != clean_att:
                self.attachment.name = clean_att

        if hasattr(self, 'cover_image') and self.cover_image and getattr(self.cover_image, 'name', None):
            clean_cov = sanitize_filename(self.cover_image.name)
            if self.cover_image.name != clean_cov:
                self.cover_image.name = clean_cov

        super().save(*args, **kwargs)


class TaskField(models.Model):
    """Custom dynamic field for a task."""
    
    FIELD_TYPE_CHOICES = (
        ('text', 'Short Text'),
        ('number', 'Number'),
        ('textarea', 'Long Text'),
        ('select', 'Dropdown / Multiple Choice'),
        ('checkbox', 'Single Checkbox (Boolean)'),
        ('checkbox_group', 'Multi-Selection Checkboxes'),
        ('radio', 'Radio Buttons'),
        ('date', 'Date Input'),
        ('file', 'File Upload'),
        ('section', 'Section / Page Break'),
    )
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='custom_fields')
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default='text')
    options = models.TextField(blank=True, help_text='Comma-separated options for choice fields')
    required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def options_list(self):
        """Return options as a list, split by commas."""
        if self.options:
            return [o.strip() for o in self.options.split(',') if o.strip()]
        return []

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.label} ({self.get_field_type_display()}) for {self.task.title}"


# ─────────────────────────────────────────────────────────────────────────────
# CORRESPONDENCE  (fully separate from Task)
# ─────────────────────────────────────────────────────────────────────────────

class Correspondence(models.Model):
    """Administrative correspondence — circulars, directives, memos, notices, decisions.
    Fully independent from the Task model.
    """

    CORRESPONDENCE_TYPE_CHOICES = (
        ('circular',  'Circular'),
        ('directive', 'Directive'),
        ('memo',      'Memo'),
        ('notice',    'Notice'),
        ('decision',  'Decision'),
    )

    PRIORITY_CHOICES = (
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('critical', 'Critical'),
    )

    STATUS_CHOICES = (
        ('active',   'Active'),
        ('archived', 'Archived'),
    )

    # Core fields
    title               = models.CharField(max_length=255)
    description         = models.TextField(blank=True, default='')
    correspondence_type = models.CharField(max_length=20, choices=CORRESPONDENCE_TYPE_CHOICES, default='memo')
    reference_number    = models.CharField(max_length=120, blank=True, null=True)
    priority            = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    deadline            = models.DateTimeField(null=True, blank=True)

    # Older installs created correspondence as a Task of type 'correspondence'; this links the mirror to it.
    legacy_task = models.OneToOneField(
        'Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='mirrored_correspondence'
    )

    # Relations
    work_module = models.ForeignKey(
        WorkModule, on_delete=models.CASCADE, null=True, blank=True,
        related_name='correspondences'
    )
    created_by  = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='created_correspondences'
    )
    assigned_to = models.ManyToManyField(
        CustomUser, blank=True, related_name='assigned_correspondences'
    )

    # Files
    attachment  = models.FileField(upload_to='correspondence_attachments/', blank=True, null=True)
    pdf_version = models.FileField(upload_to='correspondence_pdfs/', blank=True, null=True, help_text="Auto-generated PDF version of the attachment for viewing")
    cover_image = models.ImageField(upload_to='correspondence_covers/', blank=True, null=True)

    # Timestamps
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Correspondence'
        verbose_name_plural = 'Correspondences'

    def __str__(self):
        return f"{self.get_correspondence_type_display()}: {self.title}"

    # ── auto-generate PDF cover ───────────────────────────────────────────────
    def generate_cover_from_attachment(self):
        """Auto-generate a cover image from a PDF attachment when no cover exists."""
        if not convert_from_path:
            return
        if self.attachment and not self.cover_image:
            filename = self.attachment.name.lower()
            if filename.endswith('.pdf'):
                try:
                    pages = convert_from_path(self.attachment.path, first_page=1, last_page=1, size=800)
                    if pages:
                        image_io = io.BytesIO()
                        pages[0].save(image_io, format='JPEG', quality=85)
                        image_io.seek(0)
                        base_name = self.attachment.name.split('/')[-1].rsplit('.', 1)[0]
                        self.cover_image.save(f"{base_name}_cover.jpg", ContentFile(image_io.read()), save=False)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Correspondence {self.id} cover gen failed: {e}")

    def generate_pdf(self):
        """Convert attachment to PDF using LibreOffice if it's not already a PDF."""
        if not self.attachment:
            return

        filename = self.attachment.name.lower()
        if filename.endswith('.pdf'):
            # It's already a PDF, just copy it to pdf_version
            if not self.pdf_version:
                self.pdf_version.save(f"{self.attachment.name.split('/')[-1]}", self.attachment, save=False)
            return

        import tempfile
        import logging
        logger = logging.getLogger(__name__)

        try:
            # We need the absolute path to the uploaded file
            input_path = self.attachment.path
            base_name = os.path.basename(input_path)
            name_without_ext = os.path.splitext(base_name)[0]
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Run LibreOffice to convert to PDF
                cmd = [
                    'soffice',
                    '--headless',
                    '--convert-to', 'pdf',
                    '--outdir', temp_dir,
                    input_path
                ]
                
                process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if process.returncode == 0:
                    output_pdf_path = os.path.join(temp_dir, f"{name_without_ext}.pdf")
                    if os.path.exists(output_pdf_path):
                        with open(output_pdf_path, 'rb') as f:
                            self.pdf_version.save(f"{name_without_ext}.pdf", File(f), save=False)
                    else:
                        logger.error(f"LibreOffice succeeded but output PDF not found: {output_pdf_path}")
                else:
                    logger.error(f"LibreOffice conversion failed: {process.stderr.decode('utf-8')}")
                    
        except Exception as e:
            logger.error(f"Failed to convert attachment to PDF for Correspondence {self.id}: {str(e)}")

    def save(self, *args, **kwargs):
        # We need the file to exist on disc first, so save if new
        is_new = self.pk is None
        if not is_new:
            # Check if attachment changed
            old_obj = Correspondence.objects.filter(pk=self.pk).first()
            if old_obj and old_obj.attachment != self.attachment:
                self.cover_image = None
                self.pdf_version = None

        super().save(*args, **kwargs)
        
        needs_second_save = False
        
        if self.attachment and not hasattr(self.attachment, '_committed') or getattr(self.attachment, '_committed', True):
            if not self.pdf_version:
                self.generate_pdf()
                needs_second_save = True
                
        # To generate cover from PDF, we should use pdf_version if it exists
        if (self.attachment or self.pdf_version) and not self.cover_image:
            source_file = self.pdf_version if self.pdf_version else self.attachment
            filename = source_file.name.lower()
            if filename.endswith('.pdf'):
                try:
                    pages = convert_from_path(source_file.path, first_page=1, last_page=1, size=800)
                    if pages:
                        image_io = io.BytesIO()
                        pages[0].save(image_io, format='JPEG', quality=85)
                        image_io.seek(0)
                        base_name = source_file.name.split('/')[-1].rsplit('.', 1)[0]
                        self.cover_image.save(f"{base_name}_cover.jpg", ContentFile(image_io.read()), save=False)
                        needs_second_save = True
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Correspondence {self.id} cover gen failed: {e}")

        if needs_second_save:
            super().save(update_fields=['cover_image', 'pdf_version'])

    # ── helpers ───────────────────────────────────────────────────────────────
    @property
    def is_overdue(self):
        return self.deadline and timezone.now() > self.deadline

    def acknowledgement_count(self):
        return self.acknowledgements.count()

    def is_acknowledged_by(self, user):
        return self.acknowledgements.filter(user=user).exists()


class CorrespondenceAcknowledgement(models.Model):
    """Records that a specific user has acknowledged a Correspondence document."""
    correspondence = models.ForeignKey(
        Correspondence, on_delete=models.CASCADE, related_name='acknowledgements'
    )
    user        = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='corr_acknowledgements')
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    note        = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('correspondence', 'user')
        ordering = ['acknowledged_at']

    def __str__(self):
        return f"{self.user.get_full_name()} ack'd '{self.correspondence.title}'"


class CorrespondenceAttachment(models.Model):
    """Additional attachments for a correspondence document."""
    correspondence = models.ForeignKey(
        Correspondence, on_delete=models.CASCADE, related_name='attachments'
    )
    file = models.FileField(upload_to='correspondence_attachments/')
    pdf_version = models.FileField(upload_to='correspondence_pdfs/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Attachment for {self.correspondence.title}"

    def generate_pdf(self):
        """Convert attachment to PDF using LibreOffice if it's not already a PDF."""
        if not self.file:
            return

        filename = self.file.name.lower()
        if filename.endswith('.pdf'):
            if not self.pdf_version:
                self.pdf_version.save(f"{self.file.name.split('/')[-1]}", self.file, save=False)
            return

        import tempfile
        import logging
        logger = logging.getLogger(__name__)

        try:
            input_path = self.file.path
            base_name = os.path.basename(input_path)
            name_without_ext = os.path.splitext(base_name)[0]
            
            with tempfile.TemporaryDirectory() as temp_dir:
                cmd = [
                    'soffice',
                    '--headless',
                    '--convert-to', 'pdf',
                    '--outdir', temp_dir,
                    input_path
                ]
                
                process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                if process.returncode == 0:
                    output_pdf_path = os.path.join(temp_dir, f"{name_without_ext}.pdf")
                    if os.path.exists(output_pdf_path):
                        with open(output_pdf_path, 'rb') as f:
                            self.pdf_version.save(f"{name_without_ext}.pdf", File(f), save=False)
                else:
                    logger.error(f"LibreOffice conversion failed: {process.stderr.decode('utf-8')}")
                    
        except Exception as e:
            logger.error(f"Failed to convert attachment to PDF: {str(e)}")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not is_new:
            old_obj = CorrespondenceAttachment.objects.filter(pk=self.pk).first()
            if old_obj and old_obj.file != self.file:
                self.pdf_version = None

        super().save(*args, **kwargs)
        
        if self.file and getattr(self.file, '_committed', True):
            if not self.pdf_version:
                self.generate_pdf()
                if self.pdf_version:
                    super().save(update_fields=['pdf_version'])


# ─────────────────────────────────────────────────────────────────────────────
# TASK TODO  (admin-only internal planning items)
# ─────────────────────────────────────────────────────────────────────────────

class TaskTodo(models.Model):
    """Admin-only internal TODO item attached to a task.

    Used for planning, supervision, and quality control.
    Not visible to workers.
    """

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='todos')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_todos')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['task', 'status']),
        ]

    def __str__(self):
        return f"TODO: {self.title} ({self.get_status_display()}) — Task #{self.task_id}"


class TaskTodoAttachment(models.Model):
    """File attachment for a TaskTodo item."""

    todo = models.ForeignKey(TaskTodo, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='todo_attachments/')
    original_filename = models.CharField(max_length=255, blank=True, default='')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='todo_uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Attachment '{self.original_filename}' for TODO #{self.todo_id}"


# ─────────────────────────────────────────────────────────────────────────────
# MODULE TODO  (module-scoped planning items for correspondence dashboards)
# ─────────────────────────────────────────────────────────────────────────────

class Todo(models.Model):
    """Module-scoped TODO item for the administrative correspondence dashboard.

    Used for planning, tracking action items, and internal notes
    at the module level — visible only to managers and super admins.
    """

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    work_module = models.ForeignKey(WorkModule, on_delete=models.CASCADE, related_name='todos', null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='module_todos')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['work_module', 'status']),
        ]

    def __str__(self):
        mod_name = self.work_module.name if self.work_module else 'General'
        return f"TODO: {self.title} ({self.get_status_display()}) — Module: {mod_name}"


class TodoAttachment(models.Model):
    """File attachment for a Module-level Todo item."""

    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='module_todo_attachments/')
    original_filename = models.CharField(max_length=255, blank=True, default='')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='module_todo_uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Attachment '{self.original_filename}' for Todo #{self.todo_id}"
