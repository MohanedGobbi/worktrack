from django import forms
from .models import SiteConfiguration

class SiteConfigurationForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = [
            'app_name', 'app_name_ar', 'theme_mode',
            'logo', 'theme_preset', 'primary_color', 'secondary_color',
            'banner_image', 'gateway_image', 'background_image', 'font_main', 'accent_color', 'bg_color_start',
            'bg_color_end', 'glass_bg_color', 'glass_border_color', 'glass_blur',
            'glow_color', 'border_radius', 'widget_color', 'banner_text_color', 'banner_text_style',
            'button_color', 'button_hover_color', 'button_text_color',
            'sidebar_bg_color', 'sidebar_text_color', 'sidebar_muted_color', 'sidebar_primary_color', 'sidebar_button_color', 'sidebar_width',
            'portal_bg_color',
            'card_bg_color', 'text_main_color', 'text_muted_color', 'border_color',
            'success_color', 'danger_color', 'warning_color', 'info_color'
        ]
        widgets = {
            'app_name': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'e.g. Worktrack Pro'}),
            'app_name_ar': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'مثال: وورك تراك برو', 'dir': 'rtl'}),
            'theme_mode': forms.HiddenInput(attrs={'id': 'id_theme_mode'}),
            'theme_preset': forms.Select(attrs={'class': 'form-select', 'id': 'id_theme_preset'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Primary Color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Secondary Color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Accent Color'}),
            'portal_bg_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Portal Background'}),
            'bg_color_start': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Background Gradient Start'}),
            'bg_color_end': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Background Gradient End'}),
            'button_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Button Color'}),
            'button_hover_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Button Hover Color'}),
            'button_text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Button Text Color'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'banner_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'gateway_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'background_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'font_main': forms.Select(attrs={'class': 'form-select'}, choices=[
                ("'Inter', sans-serif", "Inter (Clean & Professional)"),
                ("'Roboto', sans-serif", "Roboto (Standard Corporate)"),
                ("'Plus Jakarta Sans', sans-serif", "Plus Jakarta Sans (Modern)"),
                ("'Space Grotesk', sans-serif", "Space Grotesk (Tech/Cyber)"),
                ("system-ui, -apple-system, sans-serif", "System Default (Native)")
            ]),
            'glass_bg_color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rgba(2, 44, 34, 0.65) or #022c22'}),
            'glass_border_color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rgba(255, 255, 255, 0.2) or #ffffff'}),
            'glass_blur': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'glow_color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rgba(16, 185, 129, 0.25) or #10b981'}),
            'border_radius': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '16px or 1rem'}),
            'widget_color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'rgba(2, 44, 34, 0.85) or #022c22'}),
            'banner_text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Banner Text Color'}),
            'banner_text_style': forms.Select(attrs={'class': 'form-select'}),
            'sidebar_bg_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Sidebar Base Color'}),
            'sidebar_text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Sidebar Primary Text'}),
            'sidebar_muted_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Sidebar Icon Color'}),
            'sidebar_primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Sidebar Hover/Active'}),
            'sidebar_button_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Sidebar Action Button'}),
            'sidebar_width': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 320px'}),
            'card_bg_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Card / Surface Background'}),
            'text_main_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Main Body Text Color'}),
            'text_muted_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Muted / Subtitle Text Color'}),
            'border_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Border / Divider Color'}),
            'success_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Success State Color'}),
            'danger_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Danger State Color'}),
            'warning_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Warning State Color'}),
            'info_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Info State Color'})
        }


import re as _re

_HEX = _re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')


class SiteThemeForm(forms.ModelForm):
    """Site Settings, built around the theme model: identity, three colours,
    contact and footer. The legacy colour columns stay in the database for old
    pages but are no longer edited here."""

    theme_preset = forms.ChoiceField(choices=[('rowd', 'ROWD default'), ('custom', 'Custom colours')])

    class Meta:
        model = SiteConfiguration
        fields = [
            'app_name', 'app_name_ar', 'logo', 'banner_image',
            'theme_preset', 'primary_color', 'accent_color', 'on_brand_color',
            'contact_email', 'contact_phone', 'website_url', 'address', 'address_ar',
            'footer_text', 'footer_text_ar',
            'partner_name', 'partner_name_ar', 'partner_url', 'partner_logo',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['app_name'].required = True
        for name in ('logo', 'banner_image', 'partner_logo'):
            self.fields[name].required = False
        # A legacy preset (crimson, emerald, ...) is shown as custom colours.
        if self.instance and self.instance.theme_preset not in ('rowd', 'custom'):
            self.initial['theme_preset'] = 'custom'

    def _hex(self, name, fallback):
        value = (self.cleaned_data.get(name) or '').strip()
        if not value:
            return fallback
        if not _HEX.match(value):
            raise forms.ValidationError('Use a hex colour such as #0033a0.')
        if len(value) == 4:
            value = '#' + ''.join(c * 2 for c in value[1:])
        return value.lower()

    def clean_primary_color(self):
        return self._hex('primary_color', '#0033a0')

    def clean_accent_color(self):
        return self._hex('accent_color', '#19bedc')

    def clean_on_brand_color(self):
        return self._hex('on_brand_color', '#ffffff')

    def clean_partner_logo(self):
        upload = self.cleaned_data.get('partner_logo')
        if not upload or not hasattr(upload, 'content_type'):
            return upload  # unchanged existing file
        from core.uploads import BadImage, process_photo
        try:
            return process_photo(upload, max_side=600)
        except BadImage:
            raise forms.ValidationError('Use a PNG, JPEG, GIF or WebP image under 5 MB.')

    def clean_app_name(self):
        return (self.cleaned_data.get('app_name') or '').strip()


# ── Users (Admin console > Users) ──────────────────────────────────────────

class UserAdminForm(forms.Form):
    """Create or edit a user. Roles decide privileges: a super admin gets the Django staff/superuser flags,
    everyone else has them cleared. Passwords go through the project's validators."""

    email = forms.EmailField(max_length=254)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    role = forms.ChoiceField()
    password = forms.CharField(required=False, strip=False, max_length=128)
    department = forms.ModelChoiceField(queryset=None, required=False)
    new_department = forms.CharField(max_length=255, required=False)
    manager = forms.ModelChoiceField(queryset=None, required=False)
    groups = forms.ModelMultipleChoiceField(queryset=None, required=False)
    position = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=20, required=False)
    bio = forms.CharField(max_length=2000, required=False)
    email_notifications = forms.BooleanField(required=False)
    task_notifications = forms.BooleanField(required=False)
    submission_notifications = forms.BooleanField(required=False)
    avatar = forms.FileField(required=False)

    def __init__(self, *args, instance=None, actor=None, **kwargs):
        from django.contrib.auth import get_user_model
        from users.models import Department
        from work_modules.models import WorkGroup
        User = get_user_model()
        super().__init__(*args, **kwargs)
        self.instance, self.actor = instance, actor
        self.fields['role'].choices = User.ROLE_CHOICES
        self.fields['department'].queryset = Department.objects.all()
        managers = User.objects.filter(role__in=['manager', 'super_admin'], is_active=True)
        self.fields['manager'].queryset = managers.exclude(pk=instance.pk) if instance else managers
        self.fields['groups'].queryset = WorkGroup.objects.all().order_by('order', 'name')
        if instance is None:
            self.fields['password'].required = True
            self.initial.update({'role': 'worker', 'email_notifications': True, 'task_notifications': True,
                                 'submission_notifications': True})
        else:
            profile = getattr(instance, 'profile', None)
            self.initial.update({
                'email': instance.email, 'first_name': instance.first_name, 'last_name': instance.last_name,
                'role': instance.role, 'department': instance.department_id,
                'manager': getattr(profile, 'manager_id', None), 'position': getattr(profile, 'position', ''),
                'phone': getattr(profile, 'phone', ''), 'bio': getattr(profile, 'bio', ''),
                'groups': list(instance.work_groups.values_list('pk', flat=True)),
                'email_notifications': instance.email_notifications, 'task_notifications': instance.task_notifications,
                'submission_notifications': instance.submission_notifications})

    def clean_email(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        email = User.objects.normalize_email(self.cleaned_data['email'].strip())
        taken = User.objects.filter(email__iexact=email)
        if self.instance:
            taken = taken.exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError('Another account already uses this email.')
        return email

    def clean_avatar(self):
        upload = self.cleaned_data.get('avatar')
        if not upload:
            return None
        from core.uploads import BadImage, process_photo
        try:
            return process_photo(upload)
        except BadImage:
            raise forms.ValidationError('Use a JPEG, PNG, GIF or WebP image under 5 MB.')

    def clean(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.password_validation import validate_password
        data = super().clean()
        User = get_user_model()
        password = data.get('password')
        if password:
            probe = self.instance or User(email=data.get('email') or '', first_name=data.get('first_name') or '',
                                          last_name=data.get('last_name') or '')
            try:
                validate_password(password, probe)
            except forms.ValidationError as e:
                self.add_error('password', e)
        role = data.get('role')
        if self.instance and self.instance.role == 'super_admin' and role and role != 'super_admin':
            if User.objects.filter(role='super_admin', is_active=True).exclude(pk=self.instance.pk).count() == 0:
                self.add_error('role', 'This is the only administrator. Make someone else an administrator first.')
            elif self.actor and self.instance.pk == self.actor.pk:
                self.add_error('role', 'You cannot remove your own administrator role.')
        return data

    def save(self):
        from django.contrib.auth import get_user_model
        from django.db import transaction
        from users.models import Department, UserProfile
        User = get_user_model()
        d = self.cleaned_data
        with transaction.atomic():
            user = self.instance or User()
            user.email = d['email']
            if not user.username:
                user.username = d['email'][:150]
            user.first_name, user.last_name = d['first_name'].strip(), d['last_name'].strip()
            user.role = d['role']
            is_admin = d['role'] == 'super_admin'
            user.is_superuser = user.is_staff = is_admin
            dept = d.get('department')
            if d.get('new_department', '').strip():
                dept, _ = Department.objects.get_or_create(name=d['new_department'].strip())
            user.department = dept
            for f in ('email_notifications', 'task_notifications', 'submission_notifications'):
                setattr(user, f, d[f])
            if d.get('password'):
                user.set_password(d['password'])
            elif not user.pk:
                user.set_unusable_password()
            if not user.pk and self.actor is not None:
                user.admin_owner = getattr(self.actor, 'admin_owner', None)
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.position = d['position'].strip()
            profile.phone = d['phone'].strip()
            profile.bio = d['bio'].strip()
            profile.manager = d.get('manager')
            if d.get('avatar'):
                if profile.avatar:
                    try:
                        profile.avatar.delete(save=False)
                    except Exception:
                        pass
                profile.avatar.save(d['avatar'].name, d['avatar'], save=False)
            profile.save()
            user.work_groups.set(d['groups'])
        return user


# ── Correspondence ─────────────────────────────────────────────────────────

DOCUMENT_EXTENSIONS = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.rtf',
                       '.txt', '.csv', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.zip')
MAX_DOCUMENT_BYTES = 25 * 1024 * 1024


def check_documents(files):
    """Error message for the first unacceptable uploaded document, or ''."""
    for f in files:
        name = (f.name or '').lower()
        if not name.endswith(DOCUMENT_EXTENSIONS):
            return f'"{f.name}" is not an allowed file type.'
        if f.size > MAX_DOCUMENT_BYTES:
            return f'"{f.name}" is larger than 25 MB.'
    return ''


class CorrespondenceForm(forms.Form):
    """Create / edit an administrative correspondence (circular, directive, memo, notice, decision)."""

    title = forms.CharField(max_length=255)
    description = forms.CharField(max_length=20000, required=False)
    correspondence_type = forms.ChoiceField()
    reference_number = forms.CharField(max_length=120, required=False)
    priority = forms.ChoiceField()
    deadline = forms.DateField(required=False, input_formats=['%Y-%m-%d'])
    work_module = forms.ModelChoiceField(queryset=None, required=False)
    assigned_to = forms.ModelMultipleChoiceField(queryset=None, required=False)
    status = forms.ChoiceField(required=False)
    cover_image = forms.FileField(required=False)

    def __init__(self, *args, user, instance=None, **kwargs):
        from tasks.models import Correspondence
        from work_modules.models import WorkModule
        super().__init__(*args, **kwargs)
        self.user, self.instance = user, instance
        self.fields['correspondence_type'].choices = Correspondence.CORRESPONDENCE_TYPE_CHOICES
        self.fields['priority'].choices = Correspondence.PRIORITY_CHOICES
        self.fields['status'].choices = Correspondence.STATUS_CHOICES
        if user.role == 'super_admin':
            modules = WorkModule.objects.filter(is_archived=False)
        else:
            modules = WorkModule.get_visible_modules(user).filter(is_archived=False)
        self.fields['work_module'].queryset = modules.order_by('name')
        # Recipients: the people this user works with (everyone, for a super admin).
        self.fields['assigned_to'].queryset = user.get_teammates().filter(is_active=True).order_by('first_name', 'last_name', 'email')

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise forms.ValidationError('Enter a title.')
        return title

    def clean_cover_image(self):
        upload = self.cleaned_data.get('cover_image')
        if not upload:
            return None
        from core.uploads import BadImage, process_photo
        try:
            return process_photo(upload, max_side=1200)
        except BadImage:
            raise forms.ValidationError('Use a JPEG, PNG, GIF or WebP image under 5 MB.')

    def deadline_value(self):
        """The deadline as an aware datetime at the end of the chosen day."""
        import datetime as dt
        from django.utils import timezone
        d = self.cleaned_data.get('deadline')
        return timezone.make_aware(dt.datetime.combine(d, dt.time(23, 59))) if d else None
