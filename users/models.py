from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """Custom User Manager."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom User Model with email as unique identifier."""
    
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('manager', 'Manager'),
        ('worker', 'Worker'),
    )
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='worker')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # User Preferences
    email_notifications = models.BooleanField(default=True)
    task_notifications = models.BooleanField(default=True)
    submission_notifications = models.BooleanField(default=True)
    
    THEME_CHOICES = (
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    )
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='light')
    
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('es', 'Español'),
        ('fr', 'Français'),
    )
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    
    # Platform admin flag
    is_platform_admin = models.BooleanField(default=False)
    
    # Used for Multi-Super Admin Isolation: this user belongs to this admin's environment.
    admin_owner = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='tenant_users')
    
    # Used for quick assignment in forms.
    favorite_users = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='favorited_by_users')
    
    # Custom Assigned System Profiles (Multi-profile privilege system)
    system_profiles = models.ManyToManyField('SystemProfile', blank=True, related_name='assigned_users')
    
    objects = CustomUserManager()
    
    REQUIRED_FIELDS = ['first_name', 'last_name']
    USERNAME_FIELD = 'email'
    
    def save(self, *args, **kwargs):
        """Set username to email to avoid conflicts."""
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    def get_affiliated_groups(self):
        """Returns WorkGroups this user is a member of or associated with."""
        from work_modules.models import WorkGroup
        return WorkGroup.get_user_groups(self)

    def get_teammates(self):
        """Returns users belonging to the same user groups as this user.
        Super admins see all active users.
        Managers see only users who share at least one group with them."""
        if self.role == 'super_admin' or self.is_superuser:
            return CustomUser.objects.filter(is_active=True)
        group_ids = self.work_groups.values_list('id', flat=True)
        if group_ids.exists():
            return CustomUser.objects.filter(is_active=True, work_groups__id__in=group_ids).distinct()
        affiliated_ids = self.get_affiliated_groups().values_list('id', flat=True)
        if affiliated_ids.exists():
            return CustomUser.objects.filter(is_active=True, work_groups__id__in=affiliated_ids).distinct()
        return CustomUser.objects.filter(id=self.id)

    class Meta:
        ordering = ['-created_at']


class Department(models.Model):
    """Department model for organizing users."""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    manager = models.OneToOneField(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_department')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Role(models.Model):
    """Role model for managing roles (currently for reference)."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, help_text='List of permission strings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class UserProfile(models.Model):
    """Extended user profile information."""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    position = models.CharField(max_length=255, blank=True)
    hire_date = models.DateField(default=timezone.now)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    manager = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile of {self.user.email}"
    
    class Meta:
        ordering = ['-created_at']


class SiteSettings(models.Model):
    """Global Site Settings"""
    allow_registration = models.BooleanField(default=True)
    force_language_reload = models.BooleanField(default=False, help_text="Force page reload when switching languages")
    default_language = models.CharField(max_length=10, default='ar', choices=[('ar', 'العربية (Arabic)'), ('en', 'English')], help_text="Default system language for the platform")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Site Settings"
    
    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(id=1)
        return settings


class SystemProfile(models.Model):
    """
    Custom System Profile (Privilege Profile).
    Allows creating named profiles with customizable privileges that can be assigned to users.
    """
    AVAILABLE_PRIVILEGES = [
        ('view_dashboard', 'Access Dashboards / معاينة لوحات التحكم'),
        ('manage_tasks', 'Create, Edit & Assign Tasks / إنشاء وتعديل المهام'),
        ('complete_tasks', 'Mark Tasks Completed / إتمام المهام'),
        ('manage_modules', 'Manage Directorates & Modules / إدارة الوحدات والمديريات'),
        ('manage_correspondence', 'Administrative Correspondence / المراسلات والتعميمات'),
        ('access_messenger', 'Internal Communication & Messenger / المراسلات المباشرة'),
        ('manage_attendance', 'Attendance Records & Clocking / إدارة الحضور والانصراف'),
        ('view_analytics', 'Performance Analytics & Metrics / تحليلات الأداء والإحصائيات'),
        ('manage_users', 'User Administration & Registry / إدارة المستخدمين والسجلات'),
        ('manage_intelligence', 'General Organizational Intelligence / إدارة الذكاء التنظيمي العام'),
        ('system_settings', 'System Settings & Theme Customization / إعدادات النظام وتخصيص المظهر'),
        ('export_data', 'Export Data & Reports / تصدير البيانات والتقارير'),
    ]

    name = models.CharField(max_length=150, unique=True, verbose_name='Profile Name (EN)')
    name_ar = models.CharField(max_length=150, blank=True, verbose_name='Profile Name (AR)')
    description = models.TextField(blank=True, verbose_name='Description')
    color = models.CharField(max_length=20, default='#dc2626', verbose_name='Badge Accent Color')
    privileges = models.JSONField(default=list, blank=True, help_text='List of granted permission keys')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'ملف تعريف الصلاحيات'
        verbose_name_plural = 'ملفات تعريف الصلاحيات'

    def __str__(self):
        return f"{self.name} ({self.name_ar})" if self.name_ar else self.name

    def has_privilege(self, priv_key):
        return priv_key in (self.privileges or [])


class SidebarVisibilityRule(models.Model):
    """
    Controls left sidebar features visibility per user role.
    """
    feature_key = models.CharField(max_length=60, unique=True)
    label_en = models.CharField(max_length=120)
    label_ar = models.CharField(max_length=120)
    icon = models.CharField(max_length=80, default='fas fa-circle')
    category = models.CharField(max_length=80, default='Operations')
    is_allowed = models.BooleanField(default=True, help_text='Globally enabled or disabled')
    visible_admin = models.BooleanField(default=True, help_text='Visible for Super Admins')
    visible_manager = models.BooleanField(default=True, help_text='Visible for Managers')
    visible_worker = models.BooleanField(default=True, help_text='Visible for Workers')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'قاعدة ظهور القائمة الجانبية'
        verbose_name_plural = 'قواعد ظهور القائمة الجانبية'

    def __str__(self):
        return f"{self.feature_key} - {self.label_en}"

    @classmethod
    def get_rules_map(cls):
        rules = cls.objects.all().order_by('order')
        if not rules.exists():
            cls.initialize_defaults()
            rules = cls.objects.all().order_by('order')
        return {r.feature_key: r for r in rules}

    @classmethod
    def initialize_defaults(cls):
        defaults = [
            ('home', 'Home', 'الرئيسية', 'fas fa-home', 'Command Hub', True, True, True, True, 1),
            ('dashboard', 'Dashboard', 'لوحة التحكم', 'fas fa-tachometer-alt', 'Command Hub', True, True, True, True, 2),
            ('search', 'Global Search', 'البحث الشامل', 'fas fa-search', 'Command Hub', True, True, True, True, 3),
            ('tasks', 'Active Tasks', 'المهام النشطة', 'fas fa-tasks', 'Operations', True, True, True, True, 4),
            ('kanban', 'Kanban Board', 'لوحة كانبان', 'fas fa-columns', 'Operations', True, True, True, True, 5),
            ('calendar', 'Calendar View', 'التقويم', 'fas fa-calendar-alt', 'Operations', True, True, True, True, 6),
            ('global_map', 'Global Map', 'الخريطة العالمية', 'fas fa-map-marked-alt', 'Operations', False, True, True, True, 7),
            ('modules', 'Modules', 'الوحدات', 'fas fa-bolt', 'Modules', True, True, True, False, 8),
            ('correspondence', 'Correspondence', 'المراسلات الإدارية', 'fas fa-envelope-open-text', 'Comms & Intelligence', True, True, True, True, 9),
            ('messenger', 'Messenger', 'المراسلات المباشرة', 'fas fa-comment-dots', 'Comms & Intelligence', True, True, True, True, 10),
            ('attendance', 'Attendance', 'الحضور والغياب', 'fas fa-clock', 'Comms & Intelligence', True, True, True, True, 11),
            ('metrics', 'My Metrics', 'إحصائيات الأداء', 'fas fa-chart-line', 'Comms & Intelligence', True, True, True, True, 12),
            ('team_analytics', 'Team Analytics', 'تحليلات الفريق', 'fas fa-chart-pie', 'Comms & Intelligence', True, True, True, False, 13),
            ('org_intelligence', 'Organizational Intelligence', 'الذكاء التنظيمي العام', 'fas fa-brain', 'Comms & Intelligence', False, True, True, False, 14),
            ('worker_portal', 'Worker Portal', 'بوابة الموظف', 'fas fa-hard-hat', 'Quick Access', True, True, True, True, 15),
            ('super_admin', 'Super Admin', 'لوحة الإدارة العليا', 'fas fa-crown', 'System Admin', True, True, False, False, 16),
            ('registry', 'User Registry', 'سجل المستخدمين', 'fas fa-users-cog', 'System Admin', True, True, False, False, 17),
            ('manager_portal', 'Manager Portal', 'بوابة المدير', 'fas fa-briefcase', 'System Admin', True, True, True, False, 18),
            # Off in v1 (owner decision 2026-11-07). Pages and links are gated by these keys; see core/features.py.
            ('offline_maps', 'Offline Maps', 'الخرائط دون اتصال', 'fas fa-map', 'Hidden in v1', False, True, False, False, 19),
            ('roadmap', 'Roadmap (Gantt)', 'خارطة الطريق', 'fas fa-timeline', 'Hidden in v1', False, True, True, False, 20),
            ('templates', 'Module Templates', 'قوالب الوحدات', 'fas fa-clone', 'Hidden in v1', False, True, True, False, 21),
            ('todo_management', 'To-do Management', 'إدارة المهام الصغيرة', 'fas fa-list-check', 'Hidden in v1', False, True, True, False, 22),
            ('version_archive', 'Version & Data Archive', 'أرشيف النسخ والبيانات', 'fas fa-box-archive', 'Hidden in v1', False, True, False, False, 23),
            ('host_management', 'Host Management', 'إدارة المضيفين', 'fas fa-server', 'Hidden in v1', False, True, False, False, 24),
            ('messenger_admin', 'Messenger Config and Inspect', 'إعدادات المحادثات والتدقيق', 'fas fa-comments', 'Hidden in v1', False, True, False, False, 25),
            ('translations', 'Translation Manager', 'مدير الترجمات', 'fas fa-language', 'Hidden in v1', False, True, False, False, 26),
        ]
        for key, len_str, lar_str, icon, cat, allowed, v_admin, v_mgr, v_wrk, ord_num in defaults:
            cls.objects.get_or_create(
                feature_key=key,
                defaults={
                    'label_en': len_str,
                    'label_ar': lar_str,
                    'icon': icon,
                    'category': cat,
                    'is_allowed': allowed,
                    'visible_admin': v_admin,
                    'visible_manager': v_mgr,
                    'visible_worker': v_wrk,
                    'order': ord_num
                }
            )

