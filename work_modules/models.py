from django.db import models

class TemplateModule(models.Model):
    """A reusable template for generating structured modules."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    creator = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='created_templates')
    icon_class = models.CharField(max_length=50, default='fa-folder')
    color = models.CharField(max_length=7, default='#2563eb')
    banner_image = models.ImageField(upload_to='template_banners/', blank=True, null=True)
    VISIBILITY_CHOICES = (
        ('private', 'Private to Creator'),
        ('shared', 'Shared / Assigned'),
        ('global', 'Global (All Users)'),
    )
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private')
    assigned_users = models.ManyToManyField('users.CustomUser', related_name='assigned_templates', blank=True)
    assigned_roles = models.CharField(max_length=100, blank=True, help_text="Comma-separated roles, e.g. manager,worker")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_visible_templates(cls, user):
        if getattr(user, 'role', '') == 'super_admin':
            return cls.objects.all()
        
        from django.db.models import Q
        # A template is visible if the user created it, if it's strictly global,
        # or if it's shared and explicitly assigned to them or their role.
        q = Q(creator=user) | Q(visibility='global')
        if getattr(user, 'role', ''):
            q |= Q(visibility='shared') & (Q(assigned_users=user) | Q(assigned_roles__icontains=user.role))
        else:
            q |= Q(visibility='shared') & Q(assigned_users=user)
            
        return cls.objects.filter(q).distinct()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class TemplateTask(models.Model):
    """Tasks that belong to a module template, ordered sequentially."""
    
    TASK_TYPE_CHOICES = (
        ('standard', 'Standard Task'),
        ('correspondence', 'Administrative Correspondence'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    CORRESPONDENCE_TYPE_CHOICES = (
        ('circular', 'Circular'),
        ('directive', 'Directive'),
        ('memo', 'Memo'),
        ('notice', 'Notice'),
        ('decision', 'Decision'),
    )

    template = models.ForeignKey(TemplateModule, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sequence_order = models.IntegerField(default=0, help_text="Order in the module timeline.")
    
    # Fully populated task fields
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='standard')
    correspondence_type = models.CharField(max_length=20, choices=CORRESPONDENCE_TYPE_CHOICES, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    estimated_hours = models.FloatField(default=0)
    kpi_weight = models.FloatField(default=1.0, help_text='Weight for KPI calculation')
    cover_image = models.ImageField(upload_to='template_task_covers/', blank=True, null=True)
    attachment = models.FileField(upload_to='template_task_attachments/', blank=True, null=True)
    deadline_offset_days = models.IntegerField(default=7, help_text="Days from module creation to deadline")
    checklist_items = models.JSONField(default=list, blank=True, help_text="List of sub-tasks for this unit")
    
    progress = models.IntegerField(default=0, help_text="Default progress for tasks created from this template.")
    icon_class = models.CharField(max_length=50, default='fa-tasks', help_text="Default FontAwesome icon for this unit.")
    
    class Meta:
        ordering = ['sequence_order']

    def __str__(self):
        return f"{self.title} ({self.template.name})"


class TemplateTaskField(models.Model):
    """Custom dynamic field definition for a template task."""
    
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
    
    template_task = models.ForeignKey(TemplateTask, on_delete=models.CASCADE, related_name='custom_fields')
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default='text')
    options = models.TextField(blank=True, help_text='Comma-separated options for choice fields')
    required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.label} for template {self.template_task.title}"


class TemplateTaskAttachment(models.Model):
    """Multiple attachments for a template task."""
    template_task = models.ForeignKey(TemplateTask, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='template_task_attachments/')
    filename = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename or f"Attachment {self.id} for {self.template_task.title}"


class WorkGroup(models.Model):
    """Grouping of modules with customizable aesthetics."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=50, default='fa-layer-group')
    color = models.CharField(max_length=7, default='#6366f1')
    bg_color = models.CharField(max_length=7, default='#ffffff', help_text="Background color for the group panel.")
    order = models.IntegerField(default=0)
    members = models.ManyToManyField(
        'users.CustomUser',
        blank=True,
        related_name='work_groups',
        help_text="Users belonging to this group."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']

    @classmethod
    def get_user_groups(cls, user):
        """Returns groups visible/accessible to the given user."""
        if not user.is_authenticated:
            return cls.objects.none()
        if getattr(user, 'role', '') == 'super_admin' or user.is_superuser:
            return cls.objects.all().order_by('order', 'name')
        from django.db.models import Q
        return cls.objects.filter(
            Q(members=user) |
            Q(modules__creator=user) |
            Q(modules__allowed_admins=user) |
            Q(modules__tasks__created_by=user) |
            Q(modules__tasks__assigned_to=user)
        ).distinct().order_by('order', 'name')


class WorkModule(models.Model):
    """Management of system modules."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon_class = models.CharField(max_length=50, default='fa-folder')
    color = models.CharField(max_length=7, default='#2563eb')
    description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to='module_banners/', blank=True, null=True)
    is_private = models.BooleanField(default=False, help_text="If true, only the creator and allowed admins can see this module.")
    creator = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='created_modules')
    allowed_admins = models.ManyToManyField('users.CustomUser', blank=True, related_name='accessible_modules', help_text="Admins who can access this module if it is private.")
    enrolled_users = models.ManyToManyField('users.CustomUser', blank=True, related_name='enrolled_modules', help_text="Users who have explicitly enrolled in this module.")
    group = models.CharField(max_length=100, blank=True, null=True, default='', help_text="Legacy string-based grouping.")
    group_link = models.ForeignKey(WorkGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='modules', help_text="Relationship to a managed group.")
    order = models.IntegerField(default=0)
    template = models.ForeignKey(TemplateModule, on_delete=models.SET_NULL, null=True, blank=True, related_name='instances', help_text="Template used to create this module, if any.")
    
    is_archived = models.BooleanField(default=False, help_text="If true, the module is hidden from the dashboard.")
    is_shared = models.BooleanField(default=False, help_text="If true, this module is displayed in the worker portal to all users even without assigned tasks.")
    allow_enrollment = models.BooleanField(default=False, help_text="Allow any user to self-enroll/subscribe to this module and its tasks.")
    
    # New lifecycle & progress fields
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    progress = models.IntegerField(default=0, help_text="Module completion percentage (0-100)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def contrast_text_color(self):
        """Returns '#000000' (or '#0f172a') for light module colors and '#ffffff' for dark module colors."""
        hex_color = (self.color or '#6366f1').strip().lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c * 2 for c in hex_color])
        if len(hex_color) == 6:
            try:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                # ITU-R BT.709 perceived luminance
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
                return '#0f172a' if luminance > 0.58 else '#ffffff'
            except Exception:
                pass
        return '#ffffff'

    def delete(self, *args, **kwargs):
        if self.slug == 'contact-submissions':
            from django.core.exceptions import ValidationError
            raise ValidationError("The default Contact Submissions module is protected and cannot be deleted.")
        super().delete(*args, **kwargs)
    
    class Meta:
        ordering = ['order', 'name']

    @staticmethod
    def get_visible_modules(user, include_archived=False):
        """Returns a queryset of modules visible to the given user."""
        if not user.is_authenticated:
            return WorkModule.objects.none()
        
        queryset = WorkModule.objects.all()
        if not include_archived:
            queryset = queryset.filter(is_archived=False)

        # User requested: For worker, manager, and admin portals, a module should only be displayed 
        # if it is shared (is_shared=True) AND the user has a task in it.
        # We enforce this strictly for workers and managers. For super_admins, we must still allow them 
        # to see modules they created or manage, otherwise they will be locked out of their own modules.
        
        if getattr(user, 'role', '') == 'super_admin':
            return queryset
        elif getattr(user, 'role', '') == 'manager':
            return queryset.filter(
                models.Q(creator=user) | 
                models.Q(allowed_admins=user) |
                models.Q(enrolled_users=user) |
                models.Q(tasks__assigned_to=user)
            ).distinct()
        else:
            return queryset.filter(
                models.Q(enrolled_users=user) |
                (models.Q(is_shared=True) & models.Q(tasks__assigned_to=user))
            ).distinct()

    def is_visible_to(self, user, allow_archived=False):
        """Returns True if the user can see this module."""
        if not user.is_authenticated:
            return False
        
        if self.is_archived and not allow_archived:
            # Only super admins can typically see archived modules in specific views
            if user.role != 'super_admin':
                return False

        if getattr(user, 'role', '') == 'super_admin':
            return True
        elif getattr(user, 'role', '') == 'manager':
            if self.creator == user or user in self.allowed_admins.all():
                return True
            if self.enrolled_users.filter(id=user.id).exists():
                return True
            return self.tasks.filter(assigned_to=user).exists()
        else:
            if self.enrolled_users.filter(id=user.id).exists():
                return True
            return self.is_shared and self.tasks.filter(assigned_to=user).exists()

    def get_completed_count(self):
        """Returns the number of completed tasks in this module."""
        return self.tasks.filter(status='completed').count()

    def get_total_count(self):
        """Returns the total number of tasks in this module."""
        return self.tasks.count()
