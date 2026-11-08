from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.conf import settings as django_settings
import csv
import requests
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.views import View

from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.db.models import Count, Q, F, Avg, Case, When, IntegerField
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from django.utils.text import slugify
import datetime
import os
import json
from core.sanitize import script_json
from django.core.files.base import ContentFile

from tasks.models import Task, TaskField, Correspondence, CorrespondenceAcknowledgement, CorrespondenceAttachment, TaskTodo, TaskTodoAttachment, Todo, TodoAttachment

from submissions.models import Submission, SubmissionComment, SubmissionFieldValue, SubmissionVersion
from archives.models import Document
from notifications.models import Notification
from attendance.models import AttendanceRecord
from kpi.models import UserKPI
from users.models import (
    SiteSettings, Department, UserProfile,
    SidebarVisibilityRule, SystemProfile
)
from work_modules.models import WorkModule, TemplateModule, TemplateTask, TemplateTaskAttachment, TemplateTaskField, WorkGroup
from audit.models import ActivityLog
from core.email_notifications import (
    notify,
    notify_task_assigned, 
    notify_submission_received, 
    notify_submission_reviewed,
    notify_resubmission_requested,
    notify_correspondence_acknowledged,
    notify_task_comment,
    notify_correspondence_assigned
)

User = get_user_model()


# ============= Authentication Views =============

@require_http_methods(["GET"])
@ensure_csrf_cookie
def home(request):
    """Root URL: the public landing page with sign-in built in (dashboard if signed in)."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        # Older bookmarks and forms posted credentials to "/"; keep that working.
        return login_view(request)

    from kpi.models import KPIWeight
    w = KPIWeight.get_weights()
    raw = [
        ('completion', 'Completion', 'الإنجاز', w.completion_rate_weight),
        ('on_time', 'On time', 'الالتزام بالموعد', w.on_time_rate_weight),
        ('quality', 'Quality', 'الجودة', w.quality_score_weight),
        ('productivity', 'Productivity', 'الإنتاجية', w.productivity_score_weight),
    ]
    total = sum(max(v or 0, 0) for *_, v in raw) or 1
    kpi_weights = [
        {'key': k, 'en': en, 'ar': ar, 'weight': round(v or 0, 2), 'pct': round(100 * max(v or 0, 0) / total)}
        for k, en, ar, v in raw
    ]
    return render(request, 'public/landing.html', {
        'allow_registration': SiteSettings.get_settings().allow_registration,
        'kpi_weights': kpi_weights,
    })


@require_http_methods(["GET", "POST"])
def submit_contact_message(request):
    """View to display contact admin page and receive contact messages & submissions."""
    from core.models import SiteConfiguration
    from work_modules.models import WorkModule
    from users.models import CustomUser
    from tasks.models import Task
    from notifications.models import Notification
    from django.core.mail import EmailMultiAlternatives
    from django.utils.html import strip_tags
    from django.utils import timezone
    from django.conf import settings
    import logging
    logger = logging.getLogger('django')

    site_config = SiteConfiguration.get_solo() if hasattr(SiteConfiguration, 'get_solo') else SiteConfiguration.objects.first()

    if request.method == "GET":
        context = {
            'site_config': site_config,
            'page_title': 'Contact Administration',
            'user': request.user,
        }
        return render(request, 'pages/contact_admin.html', context)

    # POST method
    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('accept', '') or
        request.POST.get('is_ajax') == '1'
    )

    try:
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        service = request.POST.get('service', '').strip()
        subject = request.POST.get('subject', '').strip()
        phone = request.POST.get('phone', '').strip()
        priority = request.POST.get('priority', 'medium').strip().lower()
        if priority not in ['low', 'medium', 'high']:
            priority = 'medium'

        # Fallbacks for authenticated users
        if request.user.is_authenticated:
            if not name:
                name = request.user.get_full_name() or request.user.username
            if not email:
                email = request.user.email

        if not name or not email or (not message and not service and not subject):
            err_msg = 'Name, Email, and Message/Service are required.'
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': err_msg}, status=400)
            messages.error(request, err_msg)
            return render(request, 'pages/contact_admin.html', {'site_config': site_config, 'error': err_msg})

        # Determine description & details
        description = f"Contact Submission: {subject or service or 'General Administration Message'}\n"
        description += f"Sender Name: {name}\n"
        description += f"Email: {email}\n"
        if phone:
            description += f"Phone: {phone}\n"
        if service:
            description += f"Requested Service: {service}\n"
        description += f"Priority: {priority.upper()}\n"
        if message:
            description += f"\n--- Message Body ---\n{message}\n"

        uploaded_file = request.FILES.get('file')
        if not uploaded_file and 'files' in request.FILES:
            files_list = request.FILES.getlist('files')
            if files_list:
                uploaded_file = files_list[0]

        if uploaded_file:
            from django.core.files.storage import default_storage
            try:
                file_name = default_storage.save(f'contact_uploads/{uploaded_file.name}', uploaded_file)
                file_url = default_storage.url(file_name)
                description += f"\nUploaded Attachment: {uploaded_file.name} (Saved as: {file_name})\nURL: {file_url}"
            except Exception as fe:
                logger.warning(f"Error storing contact upload file: {fe}")

        # IP Tracking
        ip_addr = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip_addr:
            ip_addr = ip_addr.split(',')[0].strip()
        else:
            ip_addr = request.META.get('REMOTE_ADDR', '')
            if ',' in ip_addr:
                ip_addr = ip_addr.split(',')[0].strip()

        # ActivityLog audit trail
        ActivityLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='submit',
            object_type='Contact Form',
            object_id=0,
            object_str=f"{email} ({name})",
            ip_address=ip_addr,
            description=description[:1000]
        )

        # Get or create Contact module
        contact_module, _ = WorkModule.objects.get_or_create(
            slug='contact-submissions',
            defaults={
                'name': 'Contact Submissions',
                'icon_class': 'fa-envelope-open-text',
                'color': '#9b1022',
                'description': 'Dedicated module for tracking external and internal contact form messages & service requests.',
                'is_private': False,
            }
        )

        # System user for task creation
        system_user = None
        if request.user.is_authenticated:
            system_user = request.user
        else:
            system_user = CustomUser.objects.filter(role='super_admin').order_by('id').first()
            if not system_user:
                system_user = CustomUser.objects.order_by('id').first()

        task = None
        if system_user:
            task_title = f"[{priority.upper()}] Contact: {name} - {subject or service or 'Inquiry'}"
            task = Task.objects.create(
                work_module=contact_module,
                title=task_title[:255],
                description=description,
                created_by=system_user,
                deadline=timezone.now() + timezone.timedelta(days=3),
                priority=priority,
                status='pending',
                attachment=uploaded_file,
            )

            # Assign to all Super Admins
            super_admins = CustomUser.objects.filter(role='super_admin', is_active=True)
            if super_admins.exists():
                task.assigned_to.add(*super_admins)

                # Send in-app notifications to each Super Admin
                for admin in super_admins:
                    try:
                        Notification.objects.create(
                            recipient=admin,
                            notification_type='task_created',
                            title=f"New Contact Submission: {name}",
                            message=f"[{priority.upper()}] {subject or service or 'Contact'}: {message[:120]}",
                            related_object_type='Task',
                            related_object_id=task.id,
                            is_read=False,
                        )
                    except Exception as ne:
                        logger.warning(f"Error creating admin notification: {ne}")

        # Send Automatic Email to all Super Admins
        super_admins = CustomUser.objects.filter(role='super_admin', is_active=True)
        recipient_emails = list(super_admins.exclude(email='').values_list('email', flat=True))
        if recipient_emails:
            email_subject = f"[WorkTrack Admin Alert] New Contact Submission: {name} ({priority.upper()})"
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
            
            prio_color = '#dc2626' if priority == 'high' else '#d97706' if priority == 'medium' else '#16a34a'
            html_email = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 650px; margin: 0 auto; background: #0c0f1d; color: #ffffff; border-radius: 14px; overflow: hidden; border: 1px solid #1e293b; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                <div style="background: linear-gradient(135deg, #9b1022 0%, #1e1b4b 100%); padding: 26px 30px; border-bottom: 2px solid #dc2626;">
                    <h2 style="color: #ffffff; margin: 0 0 6px; font-size: 22px; font-weight: 800; letter-spacing: -0.02em;">WorkTrack Central Administration</h2>
                    <p style="color: #fca5a5; margin: 0; font-size: 14px; font-weight: 500;">New Contact &amp; Support Submission Received</p>
                </div>
                <div style="padding: 28px 30px; background: #0c0f1d;">
                    <div style="background: #151b2e; border: 1px solid #1e293b; border-radius: 10px; padding: 18px 20px; margin-bottom: 22px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 6px 0; color: #94a3b8; font-size: 13px; width: 140px;"><strong>Sender Name:</strong></td>
                                <td style="padding: 6px 0; color: #ffffff; font-size: 14px; font-weight: 700;">{name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #94a3b8; font-size: 13px;"><strong>Email Address:</strong></td>
                                <td style="padding: 6px 0; font-size: 14px;"><a href="mailto:{email}" style="color: #38bdf8; text-decoration: none; font-weight: 600;">{email}</a></td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #94a3b8; font-size: 13px;"><strong>Phone:</strong></td>
                                <td style="padding: 6px 0; color: #e2e8f0; font-size: 14px;">{phone or 'Not provided'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #94a3b8; font-size: 13px;"><strong>Priority Level:</strong></td>
                                <td style="padding: 6px 0;">
                                    <span style="display: inline-block; background: {prio_color}; color: #ffffff; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 800; text-transform: uppercase;">{priority}</span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #94a3b8; font-size: 13px;"><strong>Subject / Topic:</strong></td>
                                <td style="padding: 6px 0; color: #f1f5f9; font-size: 14px; font-weight: 600;">{subject or service or 'General Inquiry'}</td>
                            </tr>
                        </table>
                    </div>

                    <div style="background: #111728; border-left: 4px solid #9b1022; border-radius: 6px; padding: 18px 20px; margin-bottom: 26px;">
                        <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; font-weight: 700; margin-bottom: 8px;">Message Content:</div>
                        <div style="color: #e2e8f0; font-size: 14px; line-height: 1.6; white-space: pre-wrap;">{message}</div>
                    </div>

                    <div style="text-align: center; margin-top: 25px;">
                        <a href="{site_url}/modules/contact-submissions/" style="display: inline-block; background: linear-gradient(135deg, #9b1022 0%, #dc2626 100%); color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 700; font-size: 14px; box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);">
                            Open Contact Submissions Module &rarr;
                        </a>
                    </div>
                </div>
                <div style="background: #080a14; padding: 16px 30px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #1e293b;">
                    WorkTrack Pro &bull; Automated Platform Dispatch
                </div>
            </div>
            """
            text_email = strip_tags(html_email)
            try:
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@worktrack.com')
                email_msg = EmailMultiAlternatives(
                    subject=email_subject,
                    body=text_email,
                    from_email=from_email,
                    to=recipient_emails,
                )
                email_msg.attach_alternative(html_email, "text/html")
                email_msg.send(fail_silently=True)
            except Exception as mail_err:
                logger.warning(f"Error dispatching contact email to super admins: {mail_err}")

        success_msg = 'Your message has been received and registered. Super Admins have been notified immediately.'
        if is_ajax:
            return JsonResponse({'status': 'success', 'message': success_msg})

        messages.success(request, success_msg)
        return render(request, 'pages/contact_admin.html', {
            'site_config': site_config,
            'success': True,
            'message': success_msg,
        })

    except Exception as e:
        logger.error(f"Contact form processing error: {e}", exc_info=True)
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': f'Server error: {str(e)}'}, status=500)
        messages.error(request, f'Error submitting message: {str(e)}')
        return render(request, 'pages/contact_admin.html', {'site_config': site_config, 'error': str(e)})




@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def login_view(request):
    """User login view."""
    is_preview = request.GET.get('preview') == 'true'
    if request.user.is_authenticated and not is_preview:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.email, password=password)
            
            if user is not None:
                login(request, user)
                # Log successful login telemetry securely
                try:
                    ip_addr = request.META.get('HTTP_X_FORWARDED_FOR')
                    if ip_addr:
                        ip_addr = ip_addr.split(',')[0].strip()
                    else:
                        ip_addr = request.META.get('REMOTE_ADDR', '')
                        if ',' in ip_addr:
                            ip_addr = ip_addr.split(',')[0].strip()
                            
                    ActivityLog.objects.create(
                        user=user,
                        action='login',
                        object_type='User',
                        object_id=user.id,
                        object_str=user.email,
                        ip_address=ip_addr,
                        description=request.META.get('HTTP_USER_AGENT', 'Unknown Device')[:1000]
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger('django')
                    logger.error(f'Failed to write login ActivityLog: {str(e)}')
                
                messages.success(request, f'Welcome back, {user.first_name}!')
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
    
    settings = SiteSettings.get_settings()
    return render(request, 'auth/login.html', {'allow_registration': settings.allow_registration})


@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def register_view(request):

    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    settings = SiteSettings.get_settings()
    if not settings.allow_registration:
        messages.error(request, 'Registration is currently disabled.')
        return redirect('login')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if not all([first_name, last_name, email, password1, password2]):
            messages.error(request, 'All fields are required.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            # Create user
            first_sa = User.objects.filter(role='super_admin').first()
            user = User.objects.create_user(
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                role='worker',
                admin_owner=first_sa
            )
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    
    return render(request, 'auth/register.html')


@login_required(login_url='login')
@require_http_methods(["GET"])
def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


# ============= Dashboard Views =============

def get_module_workspace_stats(user, selected_group='all'):
    """Helper to compute module statistics, groups, and progress for dashboards."""
    modules_list = WorkModule.get_visible_modules(user, include_archived=False)
    available_groups = WorkGroup.objects.all()

    if selected_group != 'all':
        modules_list = modules_list.filter(group_link__slug=selected_group)

    module_stats = []
    for wm in modules_list:
        m_tasks = Task.objects.filter(work_module=wm, task_type='standard')
        m_corr = Correspondence.objects.filter(work_module=wm)
        
        m_standard_count = m_tasks.filter(is_recurring=False).count()
        m_recurring_count = m_tasks.filter(is_recurring=True).count()
        m_total = m_standard_count + m_recurring_count
        
        m_completed = m_tasks.filter(status='completed').count()
        m_rate = round((m_completed / m_total) * 100) if m_total > 0 else 0
        m_corr_count = m_corr.count()
        
        # Todo stats for this module
        m_todos = Todo.objects.filter(work_module=wm, created_by=user)
        m_todo_count = m_todos.count()
        m_pending_todo_count = m_todos.filter(status='pending').count()
        
        module_stats.append({
            'obj': wm,
            'name': wm.slug,
            'display_name': wm.name,
            'group_obj': wm.group_link,
            'group_name': wm.group_link.name if wm.group_link else 'Uncategorized',
            'is_my_module': wm.creator == user,
            'total': m_total,
            'standard_count': m_standard_count,
            'correspondence_count': m_corr_count,
            'completed': m_completed,
            'pending': m_tasks.filter(status__in=['pending', 'in_progress']).count(),
            'rate': m_rate,
            'start_date': wm.start_date,
            'deadline': wm.deadline,
            'progress': wm.progress,
            'todo_count': m_todo_count,
            'pending_todo_count': m_pending_todo_count,
        })

    # Sort module_stats by group order so {% regroup %} in the template
    # groups them correctly (regroup only groups consecutive items).
    # Uses the group's 'order' field so drag-and-drop reordering is respected.
    module_stats.sort(key=lambda m: (
        m['group_obj'] is None,
        m['group_obj'].order if m['group_obj'] else 9999,
        m['group_obj'].name if m['group_obj'] else 'zzz',
        m['obj'].order if m.get('obj') else 9999,
    ))

    # Aggregate Group Progress
    group_progress = {}
    for g in available_groups:
        g_modules = [m for m in module_stats if m['group_obj'] == g]
        if g_modules:
            avg_progress = sum(m['rate'] for m in g_modules) / len(g_modules)
            group_progress[g.id] = round(avg_progress)
        else:
            group_progress[g.id] = 0

    return {
        'modules_list': modules_list,
        'module_stats': module_stats,
        'available_groups': available_groups,
        'selected_group': selected_group,
        'group_progress': group_progress,
        'module_count': modules_list.count(),
    }

@login_required(login_url='login')
@require_http_methods(["GET"])
def dashboard(request):
    """Main dashboard — module workspace overview for admin, portals for others."""
    user = request.user

    if user.role == 'worker':
        return redirect('worker-portal')

    # Filtering by group
    selected_group = request.GET.get('group', 'all')
    mod_data = get_module_workspace_stats(user, selected_group)
    modules_list = mod_data['modules_list']
    module_stats = mod_data['module_stats']
    available_groups = mod_data['available_groups']
    group_progress = mod_data['group_progress']

    standard_tasks = Task.objects.filter(task_type='standard', work_module__in=modules_list)
    correspondence_qs = Correspondence.objects.filter(Q(work_module__in=modules_list) | Q(created_by=user, work_module__isnull=True))

    tasks_stats = {
        'total': standard_tasks.count(),
        'pending': standard_tasks.filter(status__in=['pending', 'in_progress']).count(),
        'in_progress': standard_tasks.filter(status='in_progress').count(),
        'completed': standard_tasks.filter(status='completed').count(),
        'overdue': standard_tasks.filter(status='overdue').count(),
    }
    
    # Global Correspondence — use the new Correspondence model
    corr_stats = {
        'total': correspondence_qs.count(),
        'pending': correspondence_qs.filter(status__in=['active', 'pending']).count(),
        'completed': correspondence_qs.filter(status='archived').count(),
    }

    recent_tasks_qs = standard_tasks.select_related('created_by', 'work_module').order_by('-created_at')
    recent_corr_qs = correspondence_qs.select_related('created_by', 'work_module').order_by('-created_at')
    
    tasks_page = request.GET.get('tasks_page', 1)
    corr_page = request.GET.get('corr_page', 1)
    
    recent_tasks = Paginator(recent_tasks_qs, 10).get_page(tasks_page)
    recent_correspondence = Paginator(recent_corr_qs, 10).get_page(corr_page)
    
    # Global Todo/Notes (STITCH ENHANCEMENT: Filtering Support)
    all_visible_todos = Todo.objects.filter(created_by=user).filter(Q(work_module__in=modules_list) | Q(work_module__isnull=True))
    pending_todo_total = Todo.objects.filter(created_by=user).filter(Q(work_module__in=modules_list) | Q(work_module__isnull=True), status='pending').count()
    
    # Pass up to 30 recent todos, ignoring todo_filter so frontend can filter dynamically
    recent_todos = all_visible_todos.select_related('work_module', 'created_by').order_by('-created_at')[:30]
    
    my_submissions = Submission.objects.filter(
        Q(worker=user) | Q(task__work_module__in=modules_list)
    ).select_related('task', 'reviewed_by').distinct()

    submissions_stats = {
        'total': my_submissions.count(),
        'draft': my_submissions.filter(status='draft').count(),
        'submitted': my_submissions.filter(status='submitted').count(),
        'under_review': my_submissions.filter(status='under_review').count(),
        'approved': my_submissions.filter(status='approved').count(),
        'rejected': my_submissions.filter(status='rejected').count(),
    }
    
    # MODULE TIMELINE DATA (For Gantt Chart)
    timeline_modules = []
    today = timezone.now().date()
    current_month_index = today.month
    today_pos = ((today.month - 1) * 100 / 12) + (today.day * 100 / (12 * 31))
    
    # Use the same list of modules retrieved for the portals
    for m in modules_list:
        if m.start_date and m.deadline:
            # Calculate positions (1-12 months scale)
            # We use a 1200 unit scale for smooth positioning (100 units per month)
            start_month = m.start_date.month
            start_day = m.start_date.day
            end_month = m.deadline.month
            end_day = m.deadline.day
            
            # Start position (0 to 100%)
            # ((Month-1) * 30 + Day) / 360  approx
            start_pos = ((start_month - 1) * 100 / 12) + (start_day * 100 / (12 * 31))
            
            # End position
            end_pos = ((end_month - 1) * 100 / 12) + (end_day * 100 / (12 * 31))
            
            # Duration width
            width = end_pos - start_pos
            if width <= 0: width = 5 # Minimum visibility
            
            # Days left calculation
            days_left = (m.deadline - today).days if m.deadline >= today else 0
            
            timeline_modules.append({
                'name': m.name,
                'slug': m.slug,
                'color': m.color or '#6366f1',
                'start_pos': start_pos,
                'width': width,
                'start_date': m.start_date,
                'deadline': m.deadline,
                'progress': m.progress,
                'description': m.description,
                'icon': m.icon_class or 'fa-rocket',
                'completed_tasks': m.get_completed_count(),
                'total_tasks': m.get_total_count(),
                'days_left': days_left,
            })

    # Sort by start date to keep Gantt organized
    timeline_modules.sort(key=lambda x: x['start_date'])

    recent_notifications = Notification.objects.filter(
        recipient=user, is_read=False
    ).order_by('-created_at')[:5]
    
    # Calculate global completion rate (Weighted Task Completion)
    total_tasks_count = tasks_stats['total']
    completed_tasks_count = tasks_stats['completed']
    completion_rate = round((completed_tasks_count / total_tasks_count) * 100) if total_tasks_count > 0 else 0

    # Calculate unweighted averages (Average of Module-level percentages)
    average_module_progress = 0
    average_module_completion = 0
    if module_stats:
        # 1. Average of the manually set Progress Field
        active_progress_sum = sum(m['progress'] for m in module_stats if m['progress'] is not None)
        average_module_progress = round(active_progress_sum / len(module_stats))
        
        # 2. Average of Task Completion Rates per Module
        active_rate_sum = sum(m['rate'] for m in module_stats if m['rate'] is not None)
        average_module_completion = round(active_rate_sum / len(module_stats))

    try:
        kpi = UserKPI.objects.filter(user=user).latest('month')
    except UserKPI.DoesNotExist:
        kpi = None

    pending_submissions = Submission.objects.filter(
        status__in=['submitted', 'under_review']
    ).select_related('task', 'worker').order_by('-submitted_at')[:10]

    context = {
        'recent_tasks': recent_tasks,
        'recent_correspondence': recent_correspondence,
        'recent_todos': recent_todos,
        'pending_todo_total': pending_todo_total,
        'tasks_stats': tasks_stats,
        'corr_stats': corr_stats,
        'my_submissions': my_submissions[:3],
        'submissions_stats': submissions_stats,
        'recent_notifications': recent_notifications,
        'unread_count': Notification.objects.filter(recipient=user, is_read=False).count(),
        'kpi': kpi,
        'total_tasks': total_tasks_count,
        'pending_tasks': tasks_stats['pending'],
        'completed_tasks': completed_tasks_count,
        'total_corr': corr_stats['total'],
        'pending_corr': corr_stats['pending'],
        'completed_corr': corr_stats['completed'],
        'completion_rate': completion_rate,
        'average_module_completion': average_module_completion,
        'average_module_progress': average_module_progress,
        'pending_submissions': submissions_stats['submitted'] + submissions_stats['draft'],
        'is_manager': user.role == 'manager',
        'is_worker': False,
        'team_count': User.objects.filter(role__in=['worker', 'manager']).count() if user.role == 'super_admin' else User.objects.filter(role='worker', admin_owner=user.admin_owner).count(),
        'module_count': modules_list.count(),
        'archived_count': WorkModule.objects.filter(is_archived=True).count() if user.role == 'super_admin' else WorkModule.objects.filter(is_archived=True, creator=user).count(),
        'module_stats_list': module_stats,
        'pending_submissions_list': pending_submissions,
        'version_snapshots_count': SubmissionVersion.objects.count(),
        'available_groups': available_groups,
        'selected_group': selected_group,
        'group_progress': group_progress,
        'timeline_modules': timeline_modules,
        'current_month_index': current_month_index,
        'today_pos': today_pos,
    }

    # ── pending TODO banner data ──────────────────────────────
    if user.role == 'super_admin':
        todo_qs = TaskTodo.objects.filter(status='pending', task__work_module__is_archived=False)
    else:
        todo_qs = TaskTodo.objects.filter(status='pending', task__work_module__in=modules_list)
        
    context['pending_todos'] = todo_qs.select_related('task', 'created_by').order_by('-priority', '-created_at')[:8]
    context['pending_todo_count'] = todo_qs.count()

    context.update(_wt_home_context(user, modules_list, module_stats, standard_tasks, todo_qs, context))
    return render(request, 'pages/dashboard.html', context)


_AR_MONTHS = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
_AR_DAYS = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']


def _ar_date(d, weekday=True):
    """'الجمعة 7 نوفمبر' (or '7 نوفمبر' without the weekday)."""
    if hasattr(d, 'tzinfo') and getattr(d, 'tzinfo', None) is not None:
        d = timezone.localtime(d)
    text = f'{d.day} {_AR_MONTHS[d.month - 1]}'
    return f'{_AR_DAYS[d.weekday()]} {text}' if weekday else text


def _ar_count(n, one, two, few, many):
    """Arabic number agreement: 1 and 2 have their own forms, 3-10 take the plural, 11+ the singular accusative."""
    if n == 1:
        return one
    if n == 2:
        return two
    if 3 <= n % 100 <= 10:
        return f'{n} {few}'
    return f'{n} {many}'


def _wt_home_context(user, modules_list, module_stats, standard_tasks, todo_qs, base):
    """Read-only data for the redesigned home: roadmap rows, the 'Needs you' list and today's numbers."""
    import datetime as _dt
    from django.urls import reverse

    now = timezone.now()
    today = timezone.localdate()
    year_start = _dt.date(today.year, 1, 1)
    year_end = _dt.date(today.year, 12, 31)
    span = (year_end - year_start).days + 1

    def pct(d):
        return max(0.0, min(100.0, ((d - year_start).days) * 100.0 / span))

    review_statuses = ['submitted', 'under_review']
    reviews_qs = Submission.objects.filter(
        status__in=review_statuses, task__work_module__in=modules_list
    ).select_related('task', 'task__work_module', 'worker')
    overdue_q = Q(status='overdue') | Q(deadline__lt=now, status__in=['pending', 'in_progress'])
    overdue_qs = standard_tasks.filter(overdue_q).select_related('work_module')

    review_by_module = {r['task__work_module']: r['n'] for r in reviews_qs.order_by().values('task__work_module').annotate(n=Count('id'))}
    overdue_by_module = {r['work_module']: r['n'] for r in overdue_qs.order_by().values('work_module').annotate(n=Count('id'))}

    rows = []
    for ms in module_stats:
        m = ms['obj']
        start, end = m.start_date, m.deadline
        dated = bool(start and end and end >= start and end >= year_start and start <= year_end)
        left = pct(max(start, year_start)) if dated else 0
        right = pct(min(end, year_end)) + 100.0 / span if dated else 0
        rows.append({
            'name': m.name,
            'slug': m.slug,
            'done': ms['completed'],
            'total': ms['total'],
            'rate': ms['rate'],
            'dated': dated,
            'left': round(left, 2),
            'width': round(max(right - left, 1.5), 2) if dated else 0,
            'start': start,
            'end': end,
            'late': bool(end and end < today and ms['rate'] < 100),
            'reviews': review_by_module.get(m.id, 0),
            'overdue': overdue_by_module.get(m.id, 0),
            'chip_after': (left + max(right - left, 1.5)) < 76 if dated else True,
        })
    rows.sort(key=lambda r: (not r['dated'], r['start'] or year_end, r['name']))

    needs = []
    for s in reviews_qs.order_by('submitted_at')[:5]:
        who = s.worker.get_full_name() or s.worker.username if s.worker_id else ''
        needs.append({'kind': 'review', 'title': s.task.title, 'version': s.version, 'who': who,
                      'initials': ''.join(p[:1] for p in who.split()[:2]).upper() or '?',
                      'module': s.task.work_module.name if s.task.work_module_id else '',
                      'when': s.submitted_at, 'url': reverse('submission-detail', args=[s.id])})
    for t in overdue_qs.order_by('deadline')[:4]:
        needs.append({'kind': 'overdue', 'title': t.title, 'module': t.work_module.name if t.work_module_id else '',
                      'when': t.deadline, 'url': reverse('task-detail', args=[t.id])})
    for td in todo_qs.select_related('task')[:3]:
        needs.append({'kind': 'todo', 'title': td.title, 'module': td.task.title if td.task_id else '',
                      'when': None, 'url': reverse('task-detail', args=[td.task_id]) if td.task_id else '#'})

    review_count = reviews_qs.count()
    overdue_count = overdue_qs.count()
    hour = timezone.localtime(now).hour
    return {
        'wt_greeting': 'morning' if hour < 12 else ('afternoon' if hour < 18 else 'evening'),
        'wt_today_date': today,
        'wt_today_ar': _ar_date(today),
        'wt_review_ar': (_ar_count(review_count, 'تسليم واحد ينتظر', 'تسليمان ينتظران', 'تسليمات تنتظر', 'تسليمًا ينتظر') + ' مراجعتك') if review_count else 'لا شيء بانتظار مراجعتك',
        'wt_roadmap': {
            'year': today.year,
            'today_pct': round(pct(today) + 50.0 / span, 2),
            'month_now': today.month,
            'months': [('Jan', 'يناير'), ('Feb', 'فبراير'), ('Mar', 'مارس'), ('Apr', 'أبريل'), ('May', 'مايو'), ('Jun', 'يونيو'),
                       ('Jul', 'يوليو'), ('Aug', 'أغسطس'), ('Sep', 'سبتمبر'), ('Oct', 'أكتوبر'), ('Nov', 'نوفمبر'), ('Dec', 'ديسمبر')],
            'rows': rows,
            'dated_count': sum(1 for r in rows if r['dated']),
        },
        'wt_needs': needs[:8],
        'wt_counts': {
            'review': review_count,
            'overdue': overdue_count,
            'todo': base.get('pending_todo_count', 0),
            'total': review_count + overdue_count + base.get('pending_todo_count', 0),
            'completion': base.get('completion_rate', 0),
            'team': base.get('team_count', 0),
        },
    }


@login_required(login_url='login')
@require_http_methods(["GET"])
def roadmap_gantt(request):
    """Standalone page for the Operational Roadmap (Gantt Chart)."""
    user = request.user
    if user.role not in ['super_admin', 'manager']:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
        
    modules_list = WorkModule.get_visible_modules(request.user, include_archived=False)
    
    # MODULE TIMELINE DATA (For Gantt Chart)
    timeline_modules = []
    today = timezone.now().date()
    current_month_index = today.month
    today_pos = ((today.month - 1) * 100 / 12) + (today.day * 100 / (12 * 31))
    
    for m in modules_list:
        if m.start_date and m.deadline:
            start_month = m.start_date.month
            start_day = m.start_date.day
            end_month = m.deadline.month
            end_day = m.deadline.day
            
            start_pos = ((start_month - 1) * 100 / 12) + (start_day * 100 / (12 * 31))
            end_pos = ((end_month - 1) * 100 / 12) + (end_day * 100 / (12 * 31))
            
            width = end_pos - start_pos
            if width <= 0: width = 5
            
            days_left = (m.deadline - today).days if m.deadline >= today else 0
            
            timeline_modules.append({
                'name': m.name,
                'slug': m.slug,
                'color': m.color or '#6366f1',
                'start_pos': start_pos,
                'width': width,
                'start_date': m.start_date,
                'deadline': m.deadline,
                'progress': m.progress,
                'description': m.description,
                'icon': m.icon_class or 'fa-rocket',
                'completed_tasks': m.get_completed_count(),
                'total_tasks': m.get_total_count(),
                'days_left': days_left,
            })

    timeline_modules.sort(key=lambda x: x['start_date'])
    
    context = {
        'timeline_modules': timeline_modules,
        'current_month_index': current_month_index,
        'today_pos': today_pos,
    }
    return render(request, 'pages/roadmap.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def module_dashboard(request, module_slug):
    """Dashboard for a specific module."""
    user = request.user
    module = get_object_or_404(WorkModule, slug=module_slug)
    
    # Check visibility
    if not module.is_visible_to(request.user, allow_archived=(request.user.role == 'super_admin')):
        if module.is_archived:
            messages.error(request, "This module has been archived and is no longer accessible.")
        else:
            messages.error(request, "You do not have permission to access this private module.")
        return redirect('dashboard')

    
    # All tasks for this module
    all_module_tasks = Task.objects.filter(work_module=module)

    # Standard tasks (non-correspondence)
    module_tasks = all_module_tasks.filter(task_type='standard')
    if user.role == 'worker':
        module_tasks = module_tasks.filter(assigned_to=user)

    # Correspondence tasks
    correspondence_tasks = all_module_tasks.filter(task_type='correspondence')
    if user.role == 'worker':
        correspondence_tasks = correspondence_tasks.filter(assigned_to=user)
        
    all_standard = Task.objects.filter(work_module=module, task_type='standard')
    corr_count = Correspondence.objects.filter(work_module=module).count()
    tasks_stats = {
        'total': all_standard.count(),
        'non_recurring': all_standard.filter(is_recurring=False).count(),
        'recurring': all_standard.filter(is_recurring=True).count(),
        'pending': all_standard.filter(status='pending').count(),
        'in_progress': all_standard.filter(status='in_progress').count(),
        'completed': all_standard.filter(status__in=['completed', 'approved']).count(),
        'correspondence': corr_count,
    }
    
    # Completion rate for module (task status-based)
    total_tasks = tasks_stats['total']
    completed_tasks = tasks_stats['completed']
    completion_rate = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    # Average task progress (submission-based progress field on each task)
    from django.db.models import Avg
    avg_progress_result = module_tasks.aggregate(avg=Avg('progress'))
    avg_task_progress = round(avg_progress_result['avg'] or 0)
    
    # All tasks for this module (rendered via tabs)
    # We want to show all tasks in the list, but stats are separated
    all_tasks = module_tasks.order_by('-created_at')
    
    # Submissions for this module
    module_submissions = Submission.objects.filter(task__work_module=module, task__task_type='standard')
    if user.role == 'worker':
        module_submissions = module_submissions.filter(worker=user)
        
    submissions_stats = {
        'total': module_submissions.count(),
        'approved': module_submissions.filter(status='approved').count(),
        'pending': module_submissions.filter(status__in=['submitted', 'under_review']).count(),
    }

    # Correspondence items for this module — from the new Correspondence model
    corr_qs_module = Correspondence.objects.filter(work_module=module, status='active')
    if user.role == 'worker':
        corr_qs_module = corr_qs_module.filter(assigned_to=user)

    # Correspondence stats for this module
    correspondence_stats = {
        'total': corr_qs_module.count(),
        'active': corr_qs_module.filter(status='active').count(),
        'archived': corr_qs_module.filter(status='archived').count(),
    }

    # Annotate correspondence items with acknowledgement info
    corr_tasks_annotated = []
    for c in corr_qs_module.order_by('-created_at'):
        total_assigned = c.assigned_to.count()
        ack_count = c.acknowledgements.count()
        user_acked = c.acknowledgements.filter(user=user).exists()
        corr_tasks_annotated.append({
            'source': 'correspondence',
            'obj': c,
            'title': c.title,
            'correspondence_type': c.correspondence_type,
            'priority': c.priority,
            'deadline': c.deadline,
            'attachment': c.attachment,
            'cover_image': c.cover_image,
            'reference_number': c.reference_number,
            'created_at': c.created_at,
            'detail_url': f'/correspondence/{c.pk}/',
            'edit_url': f'/correspondence/{c.pk}/edit/',
            'total_assigned': total_assigned,
            'acknowledged_count': ack_count,
            'ack_pct': int((ack_count / total_assigned * 100)) if total_assigned > 0 else 0,
            'user_acked': user_acked,
        })
    
    # Module TODOs
    corr_todos = Todo.objects.filter(work_module=module, created_by=request.user).prefetch_related('attachments').order_by('-created_at')
    corr_todo_count = corr_todos.count()
    pending_corr_todo_count = corr_todos.filter(status='pending').count()
    corr_todos_preview = corr_todos.filter(status='pending')[:3]

    # Enrolled Team logic
    from django.db.models import Count, Q
    enrolled_team = module.enrolled_users.annotate(
        module_tasks_completed=Count('assigned_tasks', filter=Q(assigned_tasks__work_module=module, assigned_tasks__status='completed')),
        module_tasks_total=Count('assigned_tasks', filter=Q(assigned_tasks__work_module=module))
    ).order_by('first_name', 'last_name')
    # Find active users not already enrolled
    available_users = User.objects.filter(is_active=True).exclude(id__in=enrolled_team).order_by('first_name', 'last_name')

    # Task timeline (read-only): each task as a bar from its start (or creation) to its deadline
    today = timezone.localdate()
    tl_tasks = list(module_tasks.annotate(
        wt_reviews=Count('submissions', filter=Q(submissions__status__in=['submitted', 'under_review']), distinct=True)
    ).prefetch_related('assigned_to').order_by('deadline', 'id'))
    def _start(t):
        return t.start_date or timezone.localtime(t.created_at).date()
    def _end(t):
        return timezone.localtime(t.deadline).date() if t.deadline else _start(t)
    timeline = None
    if tl_tasks:
        lo = min([_start(t) for t in tl_tasks] + ([module.start_date] if module.start_date else []) + [today])
        hi = max([_end(t) for t in tl_tasks] + ([module.deadline] if module.deadline else []) + [today])
        span = max((hi - lo).days, 27) + 1
        hi = lo + datetime.timedelta(days=span - 1)
        pct = lambda d: round((d - lo).days * 100.0 / span, 2)
        ticks = []
        if span > 120:
            d = lo.replace(day=1)
            while d <= hi:
                if d >= lo:
                    ticks.append({'pct': pct(d), 'en': d.strftime('%b'), 'ar': _AR_MONTHS[d.month - 1], 'year': d.year if d.month == 1 else None})
                d = (d.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        else:
            d = lo + datetime.timedelta(days=(7 - lo.weekday()) % 7)
            while d <= hi:
                ticks.append({'pct': pct(d), 'en': f'{d.day} {d.strftime("%b")}', 'ar': f'{d.day} {_AR_MONTHS[d.month - 1]}', 'year': None})
                d += datetime.timedelta(days=7)
        rows = []
        for t in tl_tasks:
            s, e = _start(t), _end(t)
            if e < s:
                s, e = e, s
            done = t.status in ('approved', 'completed')
            rows.append({
                'task': t,
                'left': pct(s),
                'width': max(round(((e - s).days + 1) * 100.0 / span, 2), 1.5),
                'overdue': bool(t.deadline and t.deadline < timezone.now() and not done),
                'done': done,
                'reviews': t.wt_reviews,
            })
        timeline = {'rows': rows, 'ticks': ticks, 'today': pct(today) + 50.0 / span, 'start': lo, 'end': hi}
    overdue_n = sum(1 for r in (timeline['rows'] if timeline else []) if r['overdue'])

    context = {
        'wt_timeline': timeline,
        'wt_overdue': overdue_n,
        'wt_reviews': sum(r['reviews'] for r in (timeline['rows'] if timeline else [])),
        'module': module,
        'module_name': module.slug,
        'module_label': module.name,
        'module_slug': module.slug,
        'all_tasks': all_tasks,
        'stats': tasks_stats,
        'completion_rate': completion_rate,
        'avg_task_progress': avg_task_progress,
        'submissions_stats': submissions_stats,
        'all_submissions': module_submissions.select_related('task', 'worker').order_by('-created_at'),
        'correspondence_tasks': corr_tasks_annotated,
        'correspondence_count': corr_qs_module.count(),
        'correspondence_stats': correspondence_stats,
        
        # Team management
        'enrolled_team': enrolled_team,
        'available_users': available_users,
        'enrolled_users_count': enrolled_team.count(),
        
        # TODO items
        'corr_todos': corr_todos,
        'corr_todo_count': corr_todo_count,
        'pending_corr_todo_count': pending_corr_todo_count,
        'corr_todos_preview': corr_todos_preview,
    }
    
    return render(request, 'pages/module_dashboard.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def module_add_user(request, module_slug):
    """Add a user to a module's team and assign them to all standard tasks."""
    module = get_object_or_404(WorkModule, slug=module_slug)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', '')
    
    if request.user.role not in ['manager', 'super_admin']:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)
        messages.error(request, 'Permission denied.')
        return redirect('module-dashboard', module_slug=module.slug)
        
    user_id = request.POST.get('user_id')
    if not user_id:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'No user selected.'}, status=400)
        messages.error(request, 'No user selected.')
        return redirect('module-dashboard', module_slug=module.slug)
        
    from users.models import CustomUser as User
    user_to_add = get_object_or_404(User, id=user_id)
    
    # Save explicit enrollment
    module.enrolled_users.add(user_to_add)
    
    # Assign to standard tasks
    assigned_count = 0
    for task in module.tasks.all():
        if not task.assigned_to.filter(id=user_to_add.id).exists():
            task.assigned_to.add(user_to_add)
            assigned_count += 1
            
    # Assign to correspondence
    for corr in module.correspondences.all():
        if not corr.assigned_to.filter(id=user_to_add.id).exists():
            corr.assigned_to.add(user_to_add)
            
    success_msg = f"{user_to_add.get_full_name() or user_to_add.username} added to {module.name} and assigned to {assigned_count} tasks."
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': success_msg,
            'user': {
                'id': user_to_add.id,
                'name': user_to_add.get_full_name() or user_to_add.username,
                'initial': ((user_to_add.first_name[:1] if user_to_add.first_name else user_to_add.username[:1]) or 'U').upper(),
                'role': user_to_add.role,
                'role_display': user_to_add.get_role_display() if hasattr(user_to_add, 'get_role_display') else user_to_add.role.title(),
                'email': user_to_add.email or '',
                'tasks_total': module.tasks.count(),
                'tasks_completed': 0,
            }
        })

    messages.success(request, success_msg)
    return redirect('module-dashboard', module_slug=module.slug)


@login_required(login_url='login')
@require_http_methods(["POST"])
def module_remove_user(request, module_slug, user_id):
    """Remove a user from a module's team and unassign from all standard tasks."""
    module = get_object_or_404(WorkModule, slug=module_slug)
    
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('module-dashboard', module_slug=module.slug)
        
    from users.models import CustomUser as User
    user_to_remove = get_object_or_404(User, id=user_id)
    
    # Remove explicit enrollment
    module.enrolled_users.remove(user_to_remove)
    
    # 1. Delete all submissions made by the user related to this module
    from submissions.models import Submission
    deleted_submissions_count, _ = Submission.objects.filter(
        worker=user_to_remove, 
        task__work_module=module
    ).delete()
    
    # 2. Unassign from standard tasks
    unassigned_tasks_count = 0
    for task in module.tasks.all():
        if task.assigned_to.filter(id=user_to_remove.id).exists():
            task.assigned_to.remove(user_to_remove)
            unassigned_tasks_count += 1
            
    # 3. Unassign from correspondence
    for corr in module.correspondences.all():
        if corr.assigned_to.filter(id=user_to_remove.id).exists():
            corr.assigned_to.remove(user_to_remove)
            
    messages.success(request, f"{user_to_remove.get_full_name()} has been completely unenrolled from {module.name}. {unassigned_tasks_count} task assignments and {deleted_submissions_count} submissions were removed.")
    return redirect('module-dashboard', module_slug=module.slug)


@login_required(login_url='login')
@require_http_methods(["POST"])
def module_unenroll(request, module_slug):
    """Allow a user to self-unenroll from a module and scrub all assignments."""
    module = get_object_or_404(WorkModule, slug=module_slug)
    user_to_remove = request.user
    
    # Remove explicit enrollment
    module.enrolled_users.remove(user_to_remove)
    
    # 1. Delete all submissions made by the user related to this module
    from submissions.models import Submission
    deleted_submissions_count, _ = Submission.objects.filter(
        worker=user_to_remove, 
        task__work_module=module
    ).delete()
    
    # 2. Unassign from standard tasks
    unassigned_tasks_count = 0
    for task in module.tasks.all():
        if task.assigned_to.filter(id=user_to_remove.id).exists():
            task.assigned_to.remove(user_to_remove)
            unassigned_tasks_count += 1
            
    # 3. Unassign from correspondence
    for corr in module.correspondences.all():
        if corr.assigned_to.filter(id=user_to_remove.id).exists():
            corr.assigned_to.remove(user_to_remove)
            
    messages.success(request, f"You have successfully left {module.name}.")
    
    if request.user.role == 'manager':
        return redirect('manager-portal')
    return redirect('worker-portal')


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def module_create(request):
    """Create a new module."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        icon_class = request.POST.get('icon_class', 'fa-folder')
        color = request.POST.get('color', '#2563eb')
        description = request.POST.get('description', '')
        group = (request.POST.get('group') or '').strip()
        is_private = request.POST.get('is_private') in ['true', 'on']
        is_shared = request.POST.get('is_shared') in ['true', 'on']
        allow_enrollment = request.POST.get('allow_enrollment') in ['true', 'on']
        allowed_admins_ids = request.POST.getlist('allowed_admins')
        template_id = request.POST.get('template_id')
        
        start_date = request.POST.get('start_date')
        deadline = request.POST.get('deadline')
        progress = request.POST.get('progress', 0)
        
        if not name:
            messages.error(request, 'Module name is required.')
            return redirect('module-create')
            
        slug = slugify(name) or "module"
        # Ensure slug uniqueness
        base_slug = slug
        counter = 1
        while WorkModule.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        # Group handling
        group_id = request.POST.get('group_id')
        group_name = request.POST.get('group')
        group_obj = None
        
        if group_id:
            group_obj = WorkGroup.objects.filter(id=group_id).first()
        elif group_name:
            # Automatic group creation with unique slug
            g_slug = slugify(group_name) or "group"
            group_obj, created = WorkGroup.objects.get_or_create(
                name=group_name,
                defaults={'slug': g_slug}
            )
            if not created and not group_obj.slug:
                group_obj.slug = g_slug
                group_obj.save()

        template = TemplateModule.objects.filter(id=template_id).first() if template_id else None
        
        # Inherit template aesthetics if default values are used
        if template:
            if icon_class == 'fa-folder' and template.icon_class:
                icon_class = template.icon_class
            if color == '#2563eb' and template.color:
                color = template.color

        module = WorkModule.objects.create(
            name=name,
            slug=slug,
            icon_class=icon_class,
            color=color,
            description=description,
            group=group_obj.name if group_obj else '',
            group_link=group_obj,
            is_private=is_private,
            is_shared=is_shared,
            allow_enrollment=allow_enrollment,
            creator=request.user,
            template=template,
            start_date=start_date if start_date else None,
            deadline=deadline if deadline else None,
            progress=progress
        )
            
        if template:
            # Inherit banner if not provided
            if not request.FILES.get('banner_image') and template.banner_image:
                try:
                    template.banner_image.open('rb')
                    module.banner_image.save(
                        os.path.basename(template.banner_image.name), 
                        ContentFile(template.banner_image.read()), 
                        save=True
                    )
                finally:
                    template.banner_image.close()

            for t_task in template.tasks.all().order_by('sequence_order'):
                deadline = timezone.now() + datetime.timedelta(days=t_task.deadline_offset_days)
                
                if t_task.task_type == 'correspondence':
                    # Create new Correspondence object
                    obj = Correspondence.objects.create(
                        work_module=module,
                        title=t_task.title,
                        description=t_task.description,
                        correspondence_type=t_task.correspondence_type or 'memo',
                        priority=t_task.priority,
                        deadline=deadline,
                        created_by=request.user,
                        status='active'
                    )
                    # Copy primary files
                    if t_task.cover_image:
                        try:
                            t_task.cover_image.open('rb')
                            obj.cover_image.save(os.path.basename(t_task.cover_image.name), ContentFile(t_task.cover_image.read()), save=False)
                        finally: t_task.cover_image.close()
                    if t_task.attachment:
                        try:
                            t_task.attachment.open('rb')
                            obj.attachment.save(os.path.basename(t_task.attachment.name), ContentFile(t_task.attachment.read()), save=False)
                        finally: t_task.attachment.close()
                    obj.save()

                    # Copy additional attachments
                    for t_attr in t_task.attachments.all():
                        try:
                            t_attr.file.open('rb')
                            CorrespondenceAttachment.objects.create(
                                correspondence=obj,
                                file=ContentFile(t_attr.file.read(), name=t_attr.filename or os.path.basename(t_attr.file.name))
                            )
                        finally: t_attr.file.close()

                    # Note: Correspondence does not currently support dynamic TaskFields in the schema.
                    # If needed, add CorrespondenceField model and copy here.

                else:
                    # Create legacy Task object
                    obj = Task.objects.create(
                        work_module=module,
                        title=t_task.title,
                        description=t_task.description,
                        task_type=t_task.task_type,
                        priority=t_task.priority,
                        estimated_hours=t_task.estimated_hours,
                        kpi_weight=t_task.kpi_weight,
                        created_by=request.user,
                        deadline=deadline,
                        is_timeline_task=True,
                        sequence_order=t_task.sequence_order,
                        status='pending'
                    )
                    # Copy primary files
                    if t_task.cover_image:
                        try:
                            t_task.cover_image.open('rb')
                            obj.cover_image.save(os.path.basename(t_task.cover_image.name), ContentFile(t_task.cover_image.read()), save=False)
                        finally: t_task.cover_image.close()
                    if t_task.attachment:
                        try:
                            t_task.attachment.open('rb')
                            obj.attachment.save(os.path.basename(t_task.attachment.name), ContentFile(t_task.attachment.read()), save=False)
                        finally: t_task.attachment.close()
                    obj.save()

                    # Copy additional attachments to Document model
                    for t_attr in t_task.attachments.all():
                        try:
                            t_attr.file.open('rb')
                            Document.objects.create(
                                task=obj,
                                file=ContentFile(t_attr.file.read(), name=t_attr.filename or os.path.basename(t_attr.file.name)),
                                uploaded_by=request.user,
                                title=t_attr.filename or os.path.basename(t_attr.file.name),
                                original_filename=t_attr.filename or os.path.basename(t_attr.file.name),
                                file_type='task_attachment'
                            )
                        finally: t_attr.file.close()
                    
                    # Copy custom fields from template task to task instance
                    # IMPORTANT: Access related field objects through clear related_name 'custom_fields'
                    for t_field in t_task.custom_fields.all():
                        TaskField.objects.create(
                            task=obj,
                            label=t_field.label,
                            field_type=t_field.field_type,
                            options=t_field.options,
                            required=t_field.required,
                            order=t_field.order
                        )


        # Add allowed admins
        if allowed_admins_ids:
            module.allowed_admins.set(User.objects.filter(id__in=allowed_admins_ids))
        
        # Handle banner image upload (overrides template banner if provided)
        if request.FILES.get('banner_image'):
            module.banner_image = request.FILES['banner_image']
            module.save()
        
        messages.success(request, f'Module "{name}" created successfully.')
        return redirect('dashboard')
            
    # List of 200 amazing FontAwesome icons for the picker
    icon_list = [
        "fa-tasks", "fa-chart-line", "fa-users-cog", "fa-folder-open", "fa-microscope",
        "fa-money-bill-wave", "fa-file-invoice", "fa-building", "fa-id-badge", "fa-calendar-alt",
        "fa-envelope", "fa-bell", "fa-cogs", "fa-shield-alt", "fa-database",
        "fa-cloud", "fa-server", "fa-laptop", "fa-mobile-alt", "fa-print",
        "fa-search", "fa-globe", "fa-plug", "fa-bolt", "fa-lightbulb",
        "fa-briefcase", "fa-graduation-cap", "fa-book", "fa-pen", "fa-thumbtack",
        "fa-tag", "fa-shopping-cart", "fa-credit-card", "fa-wallet", "fa-piggy-bank",
        "fa-university", "fa-map-marker-alt", "fa-compass", "fa-route", "fa-truck",
        "fa-box", "fa-warehouse", "fa-tools", "fa-hammer", "fa-wrench",
        "fa-screwdriver", "fa-microchip", "fa-code", "fa-terminal", "fa-bug",
        "fa-project-diagram", "fa-sitemap", "fa-network-wired", "fa-user-tie", "fa-user-nurse",
        "fa-user-graduate", "fa-user-astronaut", "fa-user-ninja", "fa-user-secret", "fa-stethoscope",
        "fa-heartbeat", "fa-medkit", "fa-first-aid", "fa-ambulance", "fa-hospital",
        "fa-dna", "fa-atom", "fa-flask", "fa-vial", "fa-pills",
        "fa-syringe", "fa-thermometer", "fa-leaf", "fa-tree", "fa-seedling",
        "fa-sun", "fa-moon", "fa-cloud-sun", "fa-cloud-rain", "fa-snowflake",
        "fa-fire", "fa-water", "fa-mountain", "fa-anchor", "fa-ship",
        "fa-plane", "fa-car", "fa-bicycle", "fa-rocket", "fa-space-shuttle",
        "fa-star", "fa-award", "fa-medal", "fa-trophy", "fa-flag",
        "fa-camera", "fa-video", "fa-image", "fa-music", "fa-film",
        "fa-gamepad", "fa-palette", "fa-chess", "fa-dice", "fa-broadcast-tower",
        "fa-headset", "fa-microphone", "fa-calculator", "fa-memory", "fa-hdd",
        "fa-keyboard", "fa-mouse", "fa-wifi", "fa-bluetooth", "fa-broadcast-tower",
        "fa-rss", "fa-share-alt", "fa-link", "fa-anchor", "fa-lock",
        "fa-unlock", "fa-key", "fa-eye", "fa-eye-slash", "fa-low-vision",
        "fa-hand-paper", "fa-handshake", "fa-thumbs-up", "fa-thumbs-down", "fa-smile",
        "fa-frown", "fa-meh", "fa-laugh", "fa-grin", "fa-angry",
        "fa-clock", "fa-hourglass", "fa-stopwatch", "fa-history", "fa-redo",
        "fa-undo", "fa-sync", "fa-random", "fa-infinity", "fa-percent",
        "fa-plus", "fa-minus", "fa-equals", "fa-divide", "fa-times",
        "fa-calculator", "fa-briefcase-medical", "fa-clinic-medical", "fa-clipboard-check", "fa-clipboard-list",
        "fa-concierge-bell", "fa-file-signature", "fa-file-contract", "fa-file-medical", "fa-file-prescription",
        "fa-glass-cheers", "fa-heart", "fa-layer-group", "fa-mug-hot", "fa-paper-plane",
        "fa-robot", "fa-running", "fa-shapes", "fa-skull", "fa-swat-team",
        "fa-ticket-alt", "fa-tools", "fa-umbrella", "fa-utensils", "fa-walking",
        "fa-wine-glass", "fa-cannabis", "fa-cookie", "fa-hamburger", "fa-hotdog",
        "fa-ice-cream", "fa-lemon", "fa-pizza-slice", "fa-wine-bottle", "fa-apple-alt",
        "fa-carrot", "fa-cheese", "fa-coffee", "fa-bread-slice", "fa-candy-cane",
        "fa-cocktail", "fa-drumstick-bite", "fa-egg", "fa-fish", "fa-glass-martini",
        "fa-mitten", "fa-palette", "fa-parachute-box", "fa-puzzle-piece", "fa-quidditch",
        "fa-snowboarding", "fa-volleyball-ball", "fa-baseball-ball", "fa-basketball-ball", "fa-bowling-ball",
        "fa-football-ball", "fa-golf-ball", "fa-hockey-puck", "fa-table-tennis", "fa-tennis-ball"
    ]
    
    return render(request, 'pages/module_form.html', {
        'icon_list': icon_list,
        'title': 'Create New Module',
        'admins': request.user.get_teammates().filter(role__in=['super_admin', 'manager']).exclude(id=request.user.id),
        'allowed_admin_ids': [],
        'templates': TemplateModule.get_visible_templates(request.user).order_by('name'),
        'initial_group': request.GET.get('group', ''),
        'all_groups': WorkGroup.get_user_groups(request.user)
    })


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def module_edit(request, module_slug):
    """Edit an existing module."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    module = get_object_or_404(WorkModule, slug=module_slug)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        icon_class = request.POST.get('icon_class', module.icon_class)
        color = request.POST.get('color', module.color)
        description = request.POST.get('description', module.description)
        group = (request.POST.get('group') or '').strip()
        is_private = request.POST.get('is_private') == 'on'
        is_shared = request.POST.get('is_shared') == 'on'
        allow_enrollment = request.POST.get('allow_enrollment') == 'on'
        allowed_admins_ids = request.POST.getlist('allowed_admins')
        
        start_date = request.POST.get('start_date') or None
        deadline = request.POST.get('deadline') or None
        progress = int(request.POST.get('progress') or 0)
        
        if not name:
            messages.error(request, 'Module name is required.')
        else:
            module.name = name
            module.icon_class = icon_class
            module.color = color
            module.description = description
            module.start_date = start_date
            module.deadline = deadline
            module.progress = progress
            
            group_id = request.POST.get('group_id')
            if group_id:
                group_obj = WorkGroup.objects.filter(id=group_id).first()
                module.group_link = group_obj
                module.group = group_obj.name if group_obj else ''
            else:
                module.group_link = None
                module.group = ''

            module.is_private = is_private
            module.is_shared = is_shared
            module.allow_enrollment = allow_enrollment
            
            # Handle banner image: new upload or clear
            if request.FILES.get('banner_image'):
                module.banner_image = request.FILES['banner_image']
            elif request.POST.get('clear_banner_image'):
                if module.banner_image:
                    module.banner_image.delete(save=False)
                module.banner_image = None
            
            module.save()
            
            # Update allowed admins
            if allowed_admins_ids:
                module.allowed_admins.set(User.objects.filter(id__in=allowed_admins_ids))
            else:
                module.allowed_admins.clear()
                
            messages.success(request, f'Module "{name}" updated successfully.')
            return redirect('module-edit', module_slug=module.slug)
            
    # List of 200 amazing FontAwesome icons for the picker
    icon_list = [
        "fa-tasks", "fa-chart-line", "fa-users-cog", "fa-folder-open", "fa-microscope",
        "fa-money-bill-wave", "fa-file-invoice", "fa-building", "fa-id-badge", "fa-calendar-alt",
        "fa-envelope", "fa-bell", "fa-cogs", "fa-shield-alt", "fa-database",
        "fa-cloud", "fa-server", "fa-laptop", "fa-mobile-alt", "fa-print",
        "fa-search", "fa-globe", "fa-plug", "fa-bolt", "fa-lightbulb",
        "fa-briefcase", "fa-graduation-cap", "fa-book", "fa-pen", "fa-thumbtack",
        "fa-tag", "fa-shopping-cart", "fa-credit-card", "fa-wallet", "fa-piggy-bank",
        "fa-university", "fa-map-marker-alt", "fa-compass", "fa-route", "fa-truck",
        "fa-box", "fa-warehouse", "fa-tools", "fa-hammer", "fa-wrench",
        "fa-screwdriver", "fa-microchip", "fa-code", "fa-terminal", "fa-bug",
        "fa-project-diagram", "fa-sitemap", "fa-network-wired", "fa-user-tie", "fa-user-nurse",
        "fa-user-graduate", "fa-user-astronaut", "fa-user-ninja", "fa-user-secret", "fa-stethoscope",
        "fa-heartbeat", "fa-medkit", "fa-first-aid", "fa-ambulance", "fa-hospital",
        "fa-dna", "fa-atom", "fa-flask", "fa-vial", "fa-pills",
        "fa-syringe", "fa-thermometer", "fa-leaf", "fa-tree", "fa-seedling",
        "fa-sun", "fa-moon", "fa-cloud-sun", "fa-cloud-rain", "fa-snowflake",
        "fa-fire", "fa-water", "fa-mountain", "fa-anchor", "fa-ship",
        "fa-plane", "fa-car", "fa-bicycle", "fa-rocket", "fa-space-shuttle",
        "fa-star", "fa-award", "fa-medal", "fa-trophy", "fa-flag",
        "fa-camera", "fa-video", "fa-image", "fa-music", "fa-film",
        "fa-gamepad", "fa-palette", "fa-chess", "fa-dice", "fa-broadcast-tower",
        "fa-headset", "fa-microphone", "fa-calculator", "fa-memory", "fa-hdd",
        "fa-keyboard", "fa-mouse", "fa-wifi", "fa-bluetooth", "fa-broadcast-tower",
        "fa-rss", "fa-share-alt", "fa-link", "fa-anchor", "fa-lock",
        "fa-unlock", "fa-key", "fa-eye", "fa-eye-slash", "fa-low-vision",
        "fa-hand-paper", "fa-handshake", "fa-thumbs-up", "fa-thumbs-down", "fa-smile",
        "fa-frown", "fa-meh", "fa-laugh", "fa-grin", "fa-angry",
        "fa-clock", "fa-hourglass", "fa-stopwatch", "fa-history", "fa-redo",
        "fa-undo", "fa-sync", "fa-random", "fa-infinity", "fa-percent",
        "fa-plus", "fa-minus", "fa-equals", "fa-divide", "fa-times",
        "fa-calculator", "fa-briefcase-medical", "fa-clinic-medical", "fa-clipboard-check", "fa-clipboard-list",
        "fa-concierge-bell", "fa-file-signature", "fa-file-contract", "fa-file-medical", "fa-file-prescription",
        "fa-glass-cheers", "fa-heart", "fa-layer-group", "fa-mug-hot", "fa-paper-plane",
        "fa-robot", "fa-running", "fa-shapes", "fa-skull", "fa-swat-team",
        "fa-ticket-alt", "fa-tools", "fa-umbrella", "fa-utensils", "fa-walking",
        "fa-wine-glass", "fa-cannabis", "fa-cookie", "fa-hamburger", "fa-hotdog",
        "fa-ice-cream", "fa-lemon", "fa-pizza-slice", "fa-wine-bottle", "fa-apple-alt",
        "fa-carrot", "fa-cheese", "fa-coffee", "fa-bread-slice", "fa-candy-cane",
        "fa-cocktail", "fa-drumstick-bite", "fa-egg", "fa-fish", "fa-glass-martini",
        "fa-mitten", "fa-palette", "fa-parachute-box", "fa-puzzle-piece", "fa-quidditch",
        "fa-snowboarding", "fa-volleyball-ball", "fa-baseball-ball", "fa-basketball-ball", "fa-bowling-ball",
        "fa-football-ball", "fa-golf-ball", "fa-hockey-puck", "fa-table-tennis", "fa-tennis-ball"
    ]
    
    return render(request, 'pages/module_form.html', {
        'module': module,
        'icon_list': icon_list,
        'title': f'Edit Module: {module.name}',
        'admins': request.user.get_teammates().filter(role__in=['super_admin', 'manager']).exclude(id=request.user.id),
        'allowed_admin_ids': list(module.allowed_admins.values_list('id', flat=True)),
        'templates': TemplateModule.get_visible_templates(request.user).order_by('name'),
        'all_groups': WorkGroup.get_user_groups(request.user)
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def module_delete(request, module_slug):
    """Delete a module."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    module = get_object_or_404(WorkModule, slug=module_slug)
    if module.slug == 'contact-submissions':
        messages.error(request, 'The Contact Submissions module is protected and cannot be deleted.')
        return redirect('dashboard')
    name = module.name

    # Failsafe: Explicitly delete related correspondence and tasks
    # This ensures no orphaned items remain even if CASCADE settings are flaky
    Task.objects.filter(work_module=module).delete()
    Correspondence.objects.filter(work_module=module).delete()

    module.delete()
    messages.success(request, f'Module "{name}" deleted successfully.')
    return redirect('dashboard')
@login_required(login_url='login')
def manage_groups(request):
    """View to list and manage all module groups."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
        
    groups = WorkGroup.objects.all().prefetch_related('members', 'modules').order_by('order', 'name')
    
    return render(request, 'pages/group_management.html', {
        'groups': groups,
        'title': 'Manage User & Module Groups'
    })

@login_required(login_url='login')
def group_create(request):
    """Create a new module & user group."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        icon_class = request.POST.get('icon_class') or 'fa-layer-group'
        color = request.POST.get('color') or '#6366f1'
        bg_color = request.POST.get('bg_color') or '#ffffff'
        description = request.POST.get('description', '')
        
        if not name:
            messages.error(request, 'Group name is required.')
        else:
            slug = slugify(name) or "group"
            # Ensure slug uniqueness
            base_slug = slug
            counter = 1
            while WorkGroup.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                
            new_group = WorkGroup.objects.create(
                name=name,
                slug=slug,
                icon_class=icon_class,
                color=color,
                bg_color=bg_color,
                description=description
            )
            member_ids = [uid for uid in request.POST.getlist('members') if str(uid).isdigit()]
            if member_ids:
                new_group.members.set(User.objects.filter(id__in=member_ids))

            messages.success(request, f'Group "{name}" created successfully with {new_group.members.count()} members.')
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('manage-groups')

    icon_list = [
        'fa-layer-group', 'fa-folder', 'fa-briefcase', 'fa-chart-pie', 
        'fa-cog', 'fa-users', 'fa-building', 'fa-rocket', 'fa-shield-alt',
        'fa-database', 'fa-cloud', 'fa-code', 'fa-microchip', 'fa-robot',
        'fa-project-diagram', 'fa-tasks', 'fa-clipboard-list', 'fa-calendar-alt',
        'fa-envelope', 'fa-bell', 'fa-bullhorn', 'fa-lightbulb', 'fa-flask',
        'fa-laptop-code', 'fa-server', 'fa-terminal', 'fa-network-wired',
        'fa-vial', 'fa-tools', 'fa-wrench', 'fa-pills', 'fa-heartbeat',
        'fa-stethoscope', 'fa-user-md', 'fa-ambulance', 'fa-hospital'
    ]
    
    return render(request, 'pages/group_form.html', {
        'icon_list': icon_list,
        'title': 'Create New Group',
        'all_users': User.objects.filter(is_active=True).order_by('role', 'first_name', 'email'),
        'group_member_ids': []
    })


@login_required(login_url='login')
def group_edit(request, group_slug):
    """Edit an existing module & user group."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('manage-groups')
    
    group = get_object_or_404(WorkGroup, slug=group_slug)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        icon_class = request.POST.get('icon_class') or 'fa-layer-group'
        color = request.POST.get('color') or '#6366f1'
        bg_color = request.POST.get('bg_color') or '#ffffff'
        description = request.POST.get('description', '')
        
        if not name:
            messages.error(request, 'Group name is required.')
        else:
            group.name = name
            group.icon_class = icon_class
            group.color = color
            group.bg_color = bg_color
            group.description = description
            group.save()

            member_ids = [uid for uid in request.POST.getlist('members') if str(uid).isdigit()]
            group.members.set(User.objects.filter(id__in=member_ids))

            messages.success(request, f'Group "{name}" updated successfully ({group.members.count()} members).')
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('group-edit', group_slug=group.slug)

    icon_list = [
        'fa-layer-group', 'fa-folder', 'fa-briefcase', 'fa-chart-pie', 
        'fa-cog', 'fa-users', 'fa-building', 'fa-rocket', 'fa-shield-alt',
        'fa-database', 'fa-cloud', 'fa-code', 'fa-microchip', 'fa-robot',
        'fa-project-diagram', 'fa-tasks', 'fa-clipboard-list', 'fa-calendar-alt',
        'fa-envelope', 'fa-bell', 'fa-bullhorn', 'fa-lightbulb', 'fa-flask',
        'fa-laptop-code', 'fa-server', 'fa-terminal', 'fa-network-wired',
        'fa-vial', 'fa-tools', 'fa-wrench', 'fa-pills', 'fa-heartbeat',
        'fa-stethoscope', 'fa-user-md', 'fa-ambulance', 'fa-hospital'
    ]
    
    return render(request, 'pages/group_form.html', {
        'group': group,
        'icon_list': icon_list,
        'title': f'Edit Group: {group.name}',
        'all_users': User.objects.filter(is_active=True).order_by('role', 'first_name', 'email'),
        'group_member_ids': list(group.members.values_list('id', flat=True))
    })


@login_required(login_url='login')
def group_delete(request, group_slug):
    """Delete a module group."""
    if request.user.role != 'super_admin':
        messages.error(request, 'Permission denied.')
        return redirect('manage-groups')
    
    group = get_object_or_404(WorkGroup, slug=group_slug)
    name = group.name
    
    # Modules will have group_link set to NULL due to SET_NULL on_delete
    group.delete()
    messages.success(request, f'Group "{name}" deleted successfully.')
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('manage-groups')



@login_required(login_url='login')
@require_http_methods(["POST"])
def module_bulk_action(request):
    """Handle bulk actions for modules: delete or export."""
    if request.user.role != 'super_admin':
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    action = request.POST.get('action')
    slugs_str = request.POST.get('module_slugs', '')
    slugs = [s.strip() for s in slugs_str.split(',') if s.strip()]
    
    if not slugs:
        messages.warning(request, 'No modules selected.')
        return redirect('dashboard')
    
    modules = WorkModule.objects.filter(slug__in=slugs)
    
    # Determine where to redirect after action — back to archive vault if that's where we came from
    referer = request.META.get('HTTP_REFERER', '')
    came_from_archive = 'archived' in referer

    if action == 'delete':
        if modules.filter(slug='contact-submissions').exists():
            messages.error(request, 'The default Contact Submissions module is protected and cannot be deleted.')
            return redirect('archived-modules') if came_from_archive else redirect('dashboard')
        count = modules.count()
        # Explicitly delete related items as per manual delete logic
        Task.objects.filter(work_module__in=modules).delete()
        Correspondence.objects.filter(work_module__in=modules).delete()
        modules.delete()
        messages.success(request, f'Successfully deleted {count} modules.')
        return redirect('archived-modules') if came_from_archive else redirect('dashboard')
    
    elif action == 'archive':
        count = modules.update(is_archived=True)
        messages.success(request, f'Successfully archived {count} modules.')
        return redirect('dashboard')
    
    elif action == 'unarchive':
        count = modules.update(is_archived=False)
        messages.success(request, f'Successfully restored {count} modules.')
        return redirect('archived-modules') if came_from_archive else redirect('dashboard')
    
    elif action == 'export':
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="modules_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Slug', 'Description', 'Creator', 'Created At', 'Total Tasks', 'Completion Rate'])
        
        for wm in modules:
            m_tasks = Task.objects.filter(work_module=wm)
            m_total = m_tasks.count()
            m_completed = m_tasks.filter(status='completed').count()
            m_rate = round((m_completed / m_total) * 100) if m_total > 0 else 0
            
            writer.writerow([
                wm.name,
                wm.slug,
                wm.description,
                wm.creator.get_full_name() if wm.creator else 'N/A',
                wm.created_at.strftime('%Y-%m-%d %H:%M'),
                m_total,
                f"{m_rate}%"
            ])
            
        return response
    
    messages.error(request, 'Invalid action.')
    return redirect('dashboard')


@login_required(login_url='login')
@require_http_methods(["GET"])
def archived_modules(request):
    """View to see and manage archived modules."""
    if request.user.role != 'super_admin':
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    modules_list = WorkModule.get_visible_modules(request.user, include_archived=True).filter(is_archived=True)
    module_stats = []
    for wm in modules_list:
        m_tasks = Task.objects.filter(work_module=wm)
        m_total = m_tasks.count()
        m_completed = m_tasks.filter(status='completed').count()
        m_rate = round((m_completed / m_total) * 100) if m_total > 0 else 0
        m_corr_count = Correspondence.objects.filter(work_module=wm).count()
        
        module_stats.append({
            'obj': wm,
            'name': wm.slug,
            'display_name': wm.name,
            'total': m_total,
            'standard_count': m_tasks.filter(task_type='standard').count(),
            'correspondence_count': m_corr_count,
            'completed': m_completed,
            'pending': m_tasks.filter(status__in=['pending', 'in_progress']).count(),
            'rate': m_rate,
        })
        
    return render(request, 'pages/archived_modules.html', {
        'module_stats_list': module_stats,
        'module_count': modules_list.count()
    })


import json

@login_required(login_url='login')
@require_http_methods(["GET"])
def template_dashboard(request):
    """Dashboard for managing Module Templates."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    search_query = request.GET.get('search', '')
    templates = TemplateModule.get_visible_templates(request.user).prefetch_related('tasks')
    
    if search_query:
        templates = templates.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    templates = templates.order_by('-created_at')
    
    # Pagination: 10 per page
    paginator = Paginator(templates, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'templates': page_obj,
        'search_query': search_query,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    return render(request, 'pages/template_dashboard.html', context)

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def template_create(request):
    """Create a new Template Module."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        icon_class = request.POST.get('icon_class', 'fa-folder')
        color = request.POST.get('color', '#2563eb')
        visibility = request.POST.get('visibility', 'private')
        assigned_roles = request.POST.getlist('assigned_roles')
        assigned_user_ids = request.POST.getlist('assigned_users')
        
        if not name:
            messages.error(request, 'Template name is required.')
        else:
            template = TemplateModule.objects.create(
                name=name,
                description=description,
                icon_class=icon_class,
                color=color,
                creator=request.user,
                visibility=visibility,
                assigned_roles=",".join(assigned_roles)
            )
            template.assigned_users.set(User.objects.filter(id__in=assigned_user_ids))
            
            if 'banner_image' in request.FILES:
                template.banner_image = request.FILES['banner_image']
                template.save()
            messages.success(request, f'Template "{name}" created successfully.')
            return redirect('template-dashboard')
            
    # Include some relevant icons
    icon_list = [
        "fa-tasks", "fa-chart-line", "fa-users-cog", "fa-folder-open", "fa-microscope",
        "fa-money-bill-wave", "fa-file-invoice", "fa-building", "fa-id-badge", "fa-calendar-alt",
        "fa-envelope", "fa-bell", "fa-cogs", "fa-shield-alt", "fa-database", "fa-cube"
    ]
    
    if request.user.role == 'super_admin':
        users = User.objects.all().exclude(id=request.user.id)
    else:
        users = User.objects.filter(admin_owner=request.user.admin_owner).exclude(id=request.user.id)
        
    return render(request, 'pages/template_form.html', {
        'title': 'Create New Template',
        'icon_list': icon_list,
        'users': users,
        'roles': ['manager', 'worker', 'super_admin']
    })

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def template_edit(request, template_id):
    """Edit an existing Template Module."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
        
    template = get_object_or_404(TemplateModule, id=template_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', template.description)
        icon_class = request.POST.get('icon_class', template.icon_class)
        color = request.POST.get('color', template.color)
        visibility = request.POST.get('visibility', template.visibility)
        assigned_roles = request.POST.getlist('assigned_roles')
        assigned_user_ids = request.POST.getlist('assigned_users')
        
        if not name:
            messages.error(request, 'Template name is required.')
        else:
            template.name = name
            template.description = description
            template.icon_class = icon_class
            template.color = color
            template.visibility = visibility
            template.assigned_roles = ",".join(assigned_roles)
            template.assigned_users.set(User.objects.filter(id__in=assigned_user_ids))
            
            if 'banner_image' in request.FILES:
                template.banner_image = request.FILES['banner_image']
            template.save()
            messages.success(request, f'Template "{name}" updated successfully.')
            return redirect('template-dashboard')
            
    icon_list = [
        "fa-tasks", "fa-chart-line", "fa-users-cog", "fa-folder-open", "fa-microscope",
        "fa-money-bill-wave", "fa-file-invoice", "fa-building", "fa-id-badge", "fa-calendar-alt",
        "fa-envelope", "fa-bell", "fa-cogs", "fa-shield-alt", "fa-database", "fa-cube"
    ]
    
    if request.user.role == 'super_admin':
        users = User.objects.all().exclude(id=request.user.id)
    else:
        users = User.objects.filter(admin_owner=request.user.admin_owner).exclude(id=request.user.id)
        
    return render(request, 'pages/template_form.html', {
        'title': f'Edit Template: {template.name}',
        'template': template,
        'icon_list': icon_list,
        'users': users,
        'assigned_user_ids': list(template.assigned_users.values_list('id', flat=True)),
        'assigned_roles': template.assigned_roles.split(',') if template.assigned_roles else [],
        'roles': ['manager', 'worker', 'super_admin']
    })

@login_required(login_url='login')
@require_http_methods(["POST"])
def template_delete(request, template_id):
    """Delete a single template."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    template = get_object_or_404(TemplateModule, id=template_id)
    name = template.name
    template.delete()
    messages.success(request, f'Template "{name}" deleted successfully.')
    return redirect('template-dashboard')

@login_required(login_url='login')
@require_http_methods(["POST"])
def template_bulk_delete(request):
    """Bulk delete multiple templates."""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    ids_raw = request.POST.get('template_ids', '')
    if ids_raw:
        ids = [int(i) for i in ids_raw.split(',') if i.isdigit()]
        count = TemplateModule.objects.filter(id__in=ids).count()
        TemplateModule.objects.filter(id__in=ids).delete()
        messages.success(request, f'Successfully deleted {count} templates.')
    else:
        messages.warning(request, 'No templates selected for deletion.')
        
    return redirect('template-dashboard')

@login_required(login_url='login')
@require_http_methods(["GET", "POST", "DELETE"])
def template_tasks_manage(request, template_id):
    """Manage tasks for a template."""
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if request.user.role not in ['manager', 'super_admin']:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
        
    template = get_object_or_404(TemplateModule, id=template_id)
    
    if request.method == 'POST':
        try:
            content_type = request.META.get('CONTENT_TYPE', '')
            # Check if this is a multipart form submission (new task with files) or a JSON sequence update
            if 'application/json' in content_type:
                data = json.loads(request.body)
                
                # Action: SEQUENCE ORDER
                if 'sequence' in data:
                    for item in data['sequence']:
                        task_id = item.get('id')
                        order = item.get('order')
                        if task_id is not None and order is not None:
                            TemplateTask.objects.filter(id=task_id, template=template).update(sequence_order=order)
                    return JsonResponse({'status': 'success'})
                
                # Action: CLONE TASK
                if data.get('action') == 'clone':
                    task_id = data.get('task_id')
                    original = get_object_or_404(TemplateTask, id=task_id, template=template)
                    
                    # Create copy
                    new_order = template.tasks.count()
                    clone = TemplateTask.objects.create(
                        template=template,
                        title=f"{original.title} (Copy)",
                        description=original.description,
                        task_type=original.task_type,
                        correspondence_type=original.correspondence_type,
                        priority=original.priority,
                        estimated_hours=original.estimated_hours,
                        kpi_weight=original.kpi_weight,
                        deadline_offset_days=original.deadline_offset_days,
                        sequence_order=new_order,
                        progress=original.progress,
                        icon_class=original.icon_class
                    )
                    
                    for attr in original.attachments.all():
                        TemplateTaskAttachment.objects.create(
                            template_task=clone,
                            file=attr.file,
                            filename=attr.filename
                        )
                    
                    # Copy custom fields
                    for field in original.custom_fields.all():
                        TemplateTaskField.objects.create(
                            template_task=clone,
                            label=field.label,
                            field_type=field.field_type,
                            options=field.options,
                            required=field.required,
                            order=field.order
                        )
                    
                    return JsonResponse({'status': 'success', 'task_id': clone.id})
                
                # Removed dangerous legacy erase-and-replace block that used to delete all tasks.
                # Use single task updates or sequence order updates instead.
                
            # If not JSON, process as FormData (Single task creation/update with files)
            task_id = request.POST.get('id')
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            task_type = request.POST.get('task_type', 'standard')
            correspondence_type = request.POST.get('correspondence_type') or None
            priority = request.POST.get('priority', 'medium')
            
            try:
                estimated_hours = float(request.POST.get('estimated_hours', 0) or 0)
            except ValueError:
                estimated_hours = 0
                
            try:
                kpi_weight = float(request.POST.get('kpi_weight', 1.0) or 1.0)
            except ValueError:
                kpi_weight = 1.0
                
            try:
                deadline_offset_days = int(request.POST.get('deadline_offset_days', 7) or 7)
            except ValueError:
                deadline_offset_days = 7
            
            try:
                progress = int(request.POST.get('progress', 0) or 0)
            except ValueError:
                progress = 0
                
            icon_class = request.POST.get('icon_class', 'fa-tasks')
            
            if task_id and str(task_id).isdigit():
                t_task = get_object_or_404(TemplateTask, id=int(task_id), template=template)
                t_task.title = title
                t_task.description = description
                t_task.task_type = task_type
                t_task.correspondence_type = correspondence_type
                t_task.priority = priority
                t_task.estimated_hours = estimated_hours
                t_task.kpi_weight = kpi_weight
                t_task.deadline_offset_days = deadline_offset_days
                t_task.progress = progress
                t_task.icon_class = icon_class
                
                
                if 'cover_image' in request.FILES:
                    t_task.cover_image = request.FILES['cover_image']
                if 'attachment' in request.FILES:
                    t_task.attachment = request.FILES['attachment']
                t_task.save()
                
                # Handle multiple attachments
                # We expect files to be in 'attachments[]'
                files = request.FILES.getlist('attachments[]')
                for f in files:
                    TemplateTaskAttachment.objects.create(
                        template_task=t_task,
                        file=f,
                        filename=f.name
                    )
                
                # Handle dynamic fields
                fields_raw = request.POST.get('custom_fields')
                if fields_raw:
                    try:
                        fields_data = json.loads(fields_raw)
                        t_task.custom_fields.all().delete()
                        for f_data in fields_data:
                            TemplateTaskField.objects.create(
                                template_task=t_task,
                                label=f_data.get('label'),
                                field_type=f_data.get('field_type', 'text'),
                                options=f_data.get('options', ''),
                                required=f_data.get('required', False),
                                order=f_data.get('order', 0)
                            )
                    except json.JSONDecodeError:
                        pass
            else:
                try:
                    max_order = template.tasks.order_by('-sequence_order').first().sequence_order
                except AttributeError:
                    max_order = -1
                    
                t_task = TemplateTask.objects.create(
                    template=template,
                    title=title,
                    description=description,
                    task_type=task_type,
                    correspondence_type=correspondence_type,
                    priority=priority,
                    estimated_hours=estimated_hours,
                    kpi_weight=kpi_weight,
                    deadline_offset_days=deadline_offset_days,
                    sequence_order=max_order + 1,
                    progress=progress,
                    icon_class=icon_class
                )
                if 'cover_image' in request.FILES:
                    t_task.cover_image = request.FILES['cover_image']
                if 'attachment' in request.FILES:
                    t_task.attachment = request.FILES['attachment']
                t_task.save()
                
                # Handle multiple attachments for new task
                files = request.FILES.getlist('attachments[]')
                for f in files:
                    TemplateTaskAttachment.objects.create(
                        template_task=t_task,
                        file=f,
                        filename=f.name
                    )
                
                # Handle dynamic fields
                fields_raw = request.POST.get('custom_fields')
                if fields_raw:
                    try:
                        fields_data = json.loads(fields_raw)
                        for f_data in fields_data:
                            TemplateTaskField.objects.create(
                                template_task=t_task,
                                label=f_data.get('label'),
                                field_type=f_data.get('field_type', 'text'),
                                options=f_data.get('options', ''),
                                required=f_data.get('required', False),
                                order=f_data.get('order', 0)
                            )
                    except json.JSONDecodeError:
                        pass
                
            # Must return the full task serialized object including media urls
            attachments_data = [{
                'id': attr.id,
                'name': attr.filename or attr.file.name.split('/')[-1],
                'url': attr.file.url
            } for attr in t_task.attachments.all()]
            
            return JsonResponse({
                'status': 'success', 
                'task': {
                    'id': t_task.id,
                    'title': t_task.title,
                    'description': t_task.description,
                    'task_type': t_task.task_type,
                    'correspondence_type': t_task.correspondence_type,
                    'priority': t_task.priority,
                    'estimated_hours': t_task.estimated_hours,
                    'kpi_weight': t_task.kpi_weight,
                    'deadline_offset_days': t_task.deadline_offset_days,
                    'sequence_order': t_task.sequence_order,
                    'cover_image': t_task.cover_image.url if t_task.cover_image else None,
                    'attachment_name': t_task.attachment.name.split('/')[-1] if t_task.attachment else None,
                    'attachments': attachments_data,
                    'progress': t_task.progress,
                    'icon_class': t_task.icon_class,
                    'custom_fields': [{
                        'id': f.id,
                        'label': f.label,
                        'field_type': f.field_type,
                        'options': f.options,
                        'required': f.required,
                        'order': f.order
                    } for f in t_task.custom_fields.all()]
                }
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        # Remove a single task
        try:
            data = json.loads(request.body)
            t_id = data.get('id')
            if not t_id:
                return JsonResponse({'status': 'error', 'message': 'Task ID is required'}, status=400)
                
            task_to_del = TemplateTask.objects.filter(id=t_id, template=template).first()
            if task_to_del:
                task_to_del.delete()
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    if is_ajax:
        tasks = template.tasks.all().order_by('sequence_order')
        tasks_list = [{
            'id': t.id, 
            'title': t.title, 
            'description': t.description, 
            'sequence_order': t.sequence_order,
            'task_type': t.task_type,
            'correspondence_type': t.correspondence_type,
            'priority': t.priority,
            'estimated_hours': t.estimated_hours,
            'kpi_weight': t.kpi_weight,
            'deadline_offset_days': t.deadline_offset_days,
            'cover_image': t.cover_image.url if t.cover_image else None,
            'attachment_name': t.attachment.name.split('/')[-1] if t.attachment else None,
            'attachments': [{
                'id': attr.id,
                'name': attr.filename or attr.file.name.split('/')[-1],
                'url': attr.file.url
            } for attr in t.attachments.all()],
            'progress': t.progress,
            'icon_class': t.icon_class,
            'custom_fields': [{
                'id': f.id,
                'label': f.label,
                'field_type': f.field_type,
                'options': f.options,
                'required': f.required,
                'order': f.order
            } for f in t.custom_fields.all()]
        } for t in tasks]
        return JsonResponse({'status': 'success', 'tasks': tasks_list})
        
    return render(request, 'pages/template_builder.html', {'template': template})


@login_required(login_url='login')
@require_http_methods(["POST"])
def update_module_order(request):
    """Update module display order via AJAX. Supports cross-group moves."""
    if request.user.role not in ['manager', 'super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        module_ids = data.get('module_ids', [])
        group_id = data.get('group_id')  # optional: target group for cross-group moves
        
        update_fields = {}
        if group_id is not None:
            if group_id in ['none', 'null', '']:
                update_fields['group_link'] = None
            else:
                try:
                    group_obj = WorkGroup.objects.get(id=int(group_id))
                    update_fields['group_link'] = group_obj
                except (WorkGroup.DoesNotExist, ValueError):
                    pass  # ignore invalid group_id, just update order
        
        for index, m_id in enumerate(module_ids):
            updates = {'order': index}
            if 'group_link' in update_fields:
                updates['group_link'] = update_fields['group_link']
            WorkModule.objects.filter(id=m_id).update(**updates)
            
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url='login')
@require_http_methods(["POST"])
def update_group_order(request):
    """Update group display order via AJAX."""
    if request.user.role not in ['manager', 'super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        group_ids = data.get('group_ids', [])
        
        for index, g_id in enumerate(group_ids):
            WorkGroup.objects.filter(id=g_id).update(order=index)
            
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url='login')
def administrative_correspondence(request):
    """Standalone administrative correspondence page.
    Shows both legacy Task-based items AND new Correspondence-model items.
    """
    user = request.user

    # ── Legacy: Task-based correspondence ───────────────────────────────────
    task_qs = Task.objects.filter(
        task_type='correspondence',
        work_module__is_archived=False
    ).select_related('work_module', 'created_by')
    
    if user.role == 'super_admin':
        pass
    elif user.role == 'manager':
        visible_modules = WorkModule.get_visible_modules(user)
        task_qs = task_qs.filter(
            Q(work_module__in=visible_modules) |
            Q(work_module__isnull=True, created_by=user) |
            Q(assigned_to=user)
        ).distinct()
    else:
        task_qs = task_qs.filter(assigned_to=user)

    module_slug = request.GET.get('module')
    selected_module = None
    if module_slug:
        selected_module = WorkModule.objects.filter(slug=module_slug).first()
        if selected_module:
            task_qs = task_qs.filter(work_module=selected_module)

    correspondence_items = []
    for ct in task_qs.order_by('-created_at'):
        total_assigned = ct.assigned_to.count()
        acknowledged_count = Submission.objects.filter(task=ct, status='approved').count()
        user_acked = Submission.objects.filter(task=ct, worker=user, status='approved').exists()

        # Find or create corresponding Correspondence model entry
        corr_match = Correspondence.objects.filter(
            Q(reference_number=ct.reference_number, reference_number__isnull=False) |
            Q(title=ct.title)
        ).first()
        if not corr_match:
            corr_match = Correspondence.objects.create(
                title=ct.title,
                description=ct.description,
                correspondence_type=ct.correspondence_type or 'memo',
                reference_number=ct.reference_number,
                priority=ct.priority,
                deadline=ct.deadline,
                work_module=ct.work_module,
                created_by=ct.created_by,
                cover_image=ct.cover_image,
                attachment=ct.attachment,
                status='active',
            )
            corr_match.assigned_to.set(ct.assigned_to.all())

        correspondence_items.append({
            'source': 'correspondence',
            'task': ct,
            'obj': corr_match,
            # unified display fields
            'title': ct.title,
            'correspondence_type': ct.correspondence_type,
            'work_module': ct.work_module,
            'priority': ct.priority,
            'deadline': ct.deadline,
            'attachment': ct.attachment,
            'cover_image': ct.cover_image,
            'reference_number': ct.reference_number,
            'created_at': ct.created_at,
            'detail_url': f'/correspondence/{corr_match.pk}/',
            'edit_url': f'/correspondence/{corr_match.pk}/edit/',
            'delete_url': f'/correspondence/{corr_match.pk}/delete/',
            # ack
            'total_assigned': total_assigned,
            'acknowledged_count': acknowledged_count,
            'ack_pct': int((acknowledged_count / total_assigned * 100)) if total_assigned > 0 else 0,
            'user_acked': user_acked,
        })

    # ── New model: Correspondence objects ────────────────────────────────────
    corr_qs = Correspondence.objects.filter(
        status='active',
        work_module__is_archived=False
    ).select_related('work_module', 'created_by')
    
    if user.role == 'super_admin':
        pass
    elif user.role == 'manager':
        visible_modules = WorkModule.get_visible_modules(user)
        corr_qs = corr_qs.filter(
            Q(work_module__in=visible_modules) |
            Q(work_module__isnull=True, created_by=user) |
            Q(assigned_to=user)
        ).distinct()
    else:
        corr_qs = corr_qs.filter(assigned_to=user)
    if selected_module:
        corr_qs = corr_qs.filter(work_module=selected_module)

    for c in corr_qs.order_by('-created_at'):
        total_assigned = c.assigned_to.count()
        ack_count = c.acknowledgements.count()
        user_acked = c.acknowledgements.filter(user=user).exists()
        correspondence_items.append({
            'source': 'correspondence',  # new model
            'task': None,
            'obj': c,
            'title': c.title,
            'correspondence_type': c.correspondence_type,
            'work_module': c.work_module,
            'priority': c.priority,
            'deadline': c.deadline,
            'attachment': c.attachment,
            'cover_image': c.cover_image,
            'reference_number': c.reference_number,
            'created_at': c.created_at,
            'detail_url': f'/correspondence/{c.pk}/',
            'edit_url': f'/correspondence/{c.pk}/edit/',
            'delete_url': f'/correspondence/{c.pk}/delete/',
            # ack
            'total_assigned': total_assigned,
            'acknowledged_count': ack_count,
            'ack_pct': int((ack_count / total_assigned * 100)) if total_assigned > 0 else 0,
            'user_acked': user_acked,
        })

    # Sort combined list by created_at desc
    correspondence_items.sort(key=lambda x: x['created_at'], reverse=True)

    # Stats
    total = len(correspondence_items)
    fully_acknowledged = sum(1 for i in correspondence_items if i['ack_pct'] == 100)
    pending_ack = sum(1 for i in correspondence_items if not i['user_acked'])
    modules_count = (
        Task.objects.filter(task_type='correspondence').values('work_module').distinct().count() +
        Correspondence.objects.values('work_module').distinct().count()
    )

    stats = {
        'total': total,
        'pending_ack': pending_ack,
        'fully_acknowledged': fully_acknowledged,
        'modules_count': modules_count,
    }

    # ── Module TODOs ────────────────────────────────────────────────────────────
    corr_todos = []
    pending_corr_todo_count = 0
    corr_todo_count = 0
    if selected_module:
        corr_todos = Todo.objects.filter(work_module=selected_module, created_by=request.user)
        # For the dashboard, only managers and super_admins should see module-level TODOs
        # assuming the template checks permissions anyway, but let's pass them
        corr_todo_count = corr_todos.count()
        pending_corr_todo_count = corr_todos.filter(status='pending').count()
        # Only show max 3 pending on the mini-panel
        corr_todos_preview = corr_todos.filter(status='pending').order_by('-priority', '-created_at')[:3]
    else:
        corr_todos_preview = []

    context = {
        'correspondence_items': correspondence_items,
        'stats': stats,
        'selected_module': selected_module,
        'corr_todos_preview': corr_todos_preview,
        'pending_corr_todo_count': pending_corr_todo_count,
        'corr_todo_count': corr_todo_count,
    }
    return render(request, 'pages/administrative_correspondence.html', context)


# ── Module TODO Views (Administrative Correspondence) ─────────────────────────

@login_required(login_url='login')
def corr_todo_management(request, module_slug):
    """Dedicated TODO management page for a specific module."""
    if request.user.role not in ['manager', 'super_admin']:
        return redirect('dashboard')
    
    module = get_object_or_404(WorkModule, slug=module_slug)
    # Prefetch attachments to avoid N+1 queries in the redesigned view
    todos = Todo.objects.filter(work_module=module, created_by=request.user).prefetch_related('attachments')
    
    total = todos.count()
    pending = todos.filter(status='pending').count()
    completed = total - pending

    context = {
        'module': module,
        'todos': todos,
        'stats': {
            'total': total,
            'pending': pending,
            'completed': completed,
        }
    }
    return render(request, 'pages/todo_management.html', context)


@login_required(login_url='login')
def organizational_intelligence_view(request):
    """
    Dedicated Executive Management Hub for General Organizational Intelligence.
    Item 7: Full track of todo tasks with metrics, filters, and full CRUD.
    """
    if request.user.role not in ['manager', 'super_admin']:
        return redirect('dashboard')
    
    modules = WorkModule.get_visible_modules(request.user)
    
    # Query parameters
    module_filter = request.GET.get('module', 'all')
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    search_query = request.GET.get('q', '').strip()
    
    todos = Todo.objects.filter(created_by=request.user).prefetch_related('attachments').select_related('work_module')
    
    if module_filter == 'general':
        todos = todos.filter(work_module__isnull=True)
    elif module_filter != 'all':
        todos = todos.filter(work_module__slug=module_filter)
    else:
        todos = todos.filter(Q(work_module__in=modules) | Q(work_module__isnull=True))
        
    if status_filter == 'pending':
        todos = todos.filter(status='pending')
    elif status_filter == 'completed':
        todos = todos.filter(status='completed')
        
    if priority_filter in ['high', 'medium', 'low']:
        todos = todos.filter(priority=priority_filter)
        
    if search_query:
        todos = todos.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))
        
    todos = todos.order_by('-priority', '-created_at')
    
    # Calculate telemetry
    all_user_todos = Todo.objects.filter(created_by=request.user)
    total_count = all_user_todos.count()
    completed_count = all_user_todos.filter(status='completed').count()
    pending_count = total_count - completed_count
    high_priority_count = all_user_todos.filter(status='pending', priority='high').count()
    efficiency_rate = round((completed_count / total_count * 100), 1) if total_count > 0 else 100.0
    
    context = {
        'todos': todos,
        'modules': modules,
        'selected_module': module_filter,
        'selected_status': status_filter,
        'selected_priority': priority_filter,
        'search_query': search_query,
        'stats': {
            'total': total_count,
            'completed': completed_count,
            'pending': pending_count,
            'high_priority': high_priority_count,
            'efficiency_rate': efficiency_rate,
        }
    }
    return render(request, 'pages/organizational_intelligence.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_toggle_complete_ajax(request, task_id):
    """
    Instantly mark a task as completed or toggle its status.
    Item 14: Quick completion with instant AJAX feedback.
    """
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if request.user.role == 'worker' and not task.assigned_to.filter(id=request.user.id).exists():
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
    if task.status in ['completed', 'approved']:
        task.status = 'in_progress'
        is_completed = False
    else:
        task.status = 'completed'
        is_completed = True
        
    task.save(update_fields=['status', 'updated_at'])
    
    msg = "Task marked as Completed" if is_completed else "Task marked as In Progress"
    return JsonResponse({
        'status': 'success',
        'task_id': task.id,
        'task_status': task.status,
        'new_status': task.status,
        'status_display': task.get_status_display(),
        'is_completed': is_completed,
        'progress': 100 if is_completed else 0,
        'message': msg
    })


@login_required(login_url='login')
def sidebar_visibility_ajax(request):
    """
    Quick Tool: Sidebar Feature Visibility Controller.
    Item 11: Full control over left side panel buttons per role.
    """
    if request.user.role != 'super_admin':
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            if data.get('reset_defaults'):
                SidebarVisibilityRule.objects.all().delete()
                SidebarVisibilityRule.initialize_defaults()
                return JsonResponse({'status': 'success', 'message': 'Sidebar defaults restored successfully'})

            rules_data = data.get('rules', [])
            if not rules_data and 'feature_key' in data:
                rules_data = [data]
            elif not rules_data and 'key' in data:
                rules_data = [{'feature_key': data['key'], **data}]

            for r_data in rules_data:
                key = r_data.get('feature_key') or r_data.get('key')
                if not key:
                    continue
                rule, _ = SidebarVisibilityRule.objects.get_or_create(feature_key=key)
                if 'is_allowed' in r_data:
                    rule.is_allowed = bool(r_data['is_allowed'])
                if 'visible_admin' in r_data:
                    rule.visible_admin = bool(r_data['visible_admin'])
                elif 'show_admin' in r_data:
                    rule.visible_admin = bool(r_data['show_admin'])
                if 'visible_manager' in r_data:
                    rule.visible_manager = bool(r_data['visible_manager'])
                elif 'show_manager' in r_data:
                    rule.visible_manager = bool(r_data['show_manager'])
                if 'visible_worker' in r_data:
                    rule.visible_worker = bool(r_data['visible_worker'])
                elif 'show_worker' in r_data:
                    rule.visible_worker = bool(r_data['show_worker'])
                rule.save()
            return JsonResponse({'status': 'success', 'message': 'Sidebar visibility rules updated successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    rules = SidebarVisibilityRule.objects.all().order_by('order')
    if not rules.exists():
        SidebarVisibilityRule.initialize_defaults()
        rules = SidebarVisibilityRule.objects.all().order_by('order')
        
    rules_list = [{
        'feature_key': r.feature_key,
        'key': r.feature_key,
        'label': r.label_en,
        'label_en': r.label_en,
        'label_ar': r.label_ar,
        'icon': r.icon,
        'category': r.category,
        'is_allowed': r.is_allowed,
        'visible_admin': r.visible_admin,
        'visible_manager': r.visible_manager,
        'visible_worker': r.visible_worker,
        'show_admin': r.visible_admin,
        'show_manager': r.visible_manager,
        'show_worker': r.visible_worker,
        'order': r.order,
    } for r in rules]
    return JsonResponse({'status': 'success', 'rules': rules_list})


@login_required(login_url='login')
def system_profiles_ajax(request):
    """
    Quick Tool: System Profiling & Privileges Manager.
    Item 12: Create/edit system profiles with custom privileges.
    """
    if request.user.role != 'super_admin':
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
    import json
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            profile_id = data.get('id')
            name = data.get('name', '').strip()
            name_ar = data.get('name_ar', '').strip()
            desc = data.get('description', '').strip()
            color = data.get('color', '#dc2626').strip()
            privs = data.get('privileges', [])
            
            if not name:
                return JsonResponse({'status': 'error', 'message': 'Profile name is required'}, status=400)
                
            if profile_id:
                prof = get_object_or_404(SystemProfile, id=profile_id)
                prof.name = name
                prof.name_ar = name_ar
                prof.description = desc
                prof.color = color
                prof.privileges = privs
                prof.save()
            else:
                prof = SystemProfile.objects.create(
                    name=name,
                    name_ar=name_ar,
                    description=desc,
                    color=color,
                    privileges=privs
                )
            return JsonResponse({'status': 'success', 'profile_id': prof.id, 'message': 'Profile saved successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        try:
            profile_id = request.GET.get('id')
            if not profile_id and request.body:
                data = json.loads(request.body)
                profile_id = data.get('id')
            if profile_id:
                prof = get_object_or_404(SystemProfile, id=profile_id)
                prof.delete()
                return JsonResponse({'status': 'success', 'message': 'Profile deleted successfully'})
            return JsonResponse({'status': 'error', 'message': 'Profile ID required'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    profiles = SystemProfile.objects.all().order_by('name')
    prof_list = [{
        'id': p.id,
        'name': p.name,
        'name_ar': p.name_ar,
        'description': p.description,
        'color': p.color,
        'privileges': p.privileges or [],
        'user_count': p.assigned_users.count(),
        'users_count': p.assigned_users.count(),
    } for p in profiles]
    
    priv_list = [{'key': k, 'label': l, 'desc': k.replace('_', ' ').title()} for k, l in SystemProfile.AVAILABLE_PRIVILEGES]
    return JsonResponse({
        'status': 'success',
        'profiles': prof_list,
        'privileges': priv_list,
        'available_privileges': priv_list
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def user_assign_profiles_ajax(request, user_id):
    """Assign system profiles to a specific user (Item 12)."""
    if request.user.role != 'super_admin':
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
    import json
    target_user = get_object_or_404(get_user_model(), id=user_id)
    try:
        data = json.loads(request.body)
        profile_ids = data.get('profile_ids', [])
        target_user.system_profiles.set(SystemProfile.objects.filter(id__in=profile_ids))
        return JsonResponse({'status': 'success', 'message': 'User profiles updated successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url='login')
def system_profiles_management(request):
    """
    Dedicated Page: System Privileges & Profiles Architecture.
    Item 5 & 6: Full-featured, elegantly styled standalone management page.
    """
    if request.user.role != 'super_admin':
        messages.error(request, 'Access restricted to Super Administrators.')
        return redirect('dashboard')

    profiles = SystemProfile.objects.all().prefetch_related('assigned_users').order_by('name')
    users = get_user_model().objects.filter(is_active=True).prefetch_related('system_profiles').order_by('role', 'username')

    categorized_privs = {
        'Operations': [
            ('view_dashboard', 'Access Dashboards / معاينة لوحات التحكم', 'fas fa-tachometer-alt'),
            ('manage_tasks', 'Create, Edit & Assign Tasks / إنشاء وتعديل المهام', 'fas fa-tasks'),
            ('complete_tasks', 'Mark Tasks Completed / إتمام المهام', 'fas fa-check-circle'),
            ('manage_modules', 'Manage Directorates & Modules / إدارة الوحدات والمديريات', 'fas fa-bolt'),
        ],
        'Communications': [
            ('manage_correspondence', 'Administrative Correspondence / المراسلات والتعميمات', 'fas fa-envelope-open-text'),
            ('access_messenger', 'Internal Communication & Messenger / المراسلات المباشرة', 'fas fa-comment-dots'),
            ('manage_intelligence', 'General Organizational Intelligence / إدارة الذكاء التنظيمي العام', 'fas fa-brain'),
        ],
        'Personnel & Analytics': [
            ('manage_attendance', 'Attendance Records & Clocking / إدارة الحضور والانصراف', 'fas fa-clock'),
            ('view_analytics', 'Performance Analytics & Metrics / تحليلات الأداء والإحصائيات', 'fas fa-chart-line'),
            ('export_data', 'Export Data & Reports / تصدير البيانات والتقارير', 'fas fa-file-export'),
        ],
        'Administration': [
            ('manage_users', 'User Administration & Registry / إدارة المستخدمين والسجلات', 'fas fa-users-cog'),
            ('system_settings', 'System Settings & Theme Customization / إعدادات النظام وتخصيص المظهر', 'fas fa-cogs'),
        ]
    }

    total_assigned_users = users.filter(system_profiles__isnull=False).distinct().count()

    context = {
        'profiles': profiles,
        'users': users,
        'categorized_privs': categorized_privs,
        'available_privileges': SystemProfile.AVAILABLE_PRIVILEGES,
        'total_profiles': profiles.count(),
        'total_assigned_users': total_assigned_users,
        'total_privileges': len(SystemProfile.AVAILABLE_PRIVILEGES),
    }
    return render(request, 'pages/system_profiles.html', context)


def _can_use_todos(user, module_slug=None, todo=None):
    """Managers and super admins manage module to-dos. Everyone else keeps personal notes:
    only general (module-less) to-dos they created themselves."""
    if user.role in ('manager', 'super_admin'):
        return True
    if todo is not None:
        return todo.work_module_id is None and todo.created_by_id == user.id
    return module_slug in ('general', 'all')


@login_required(login_url='login')
@require_http_methods(["POST"])
def corr_todo_add(request, module_slug):
    """Add a new module-level TODO with support for files and due dates."""
    if not _can_use_todos(request.user, module_slug) or (request.user.role not in ('manager', 'super_admin') and module_slug != 'general'):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    module = None
    if module_slug != 'general':
        module = get_object_or_404(WorkModule, slug=module_slug)
    
    try:
        # Using request.POST for multi-part form support (files)
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'medium')
        due_date_str = request.POST.get('due_date', '')
        
        if not title:
            return JsonResponse({'status': 'error', 'message': 'Title is required'})
            
        due_date = None
        if due_date_str:
            try:
                due_date = timezone.datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except ValueError:
                pass

        todo = Todo.objects.create(
            work_module=module,
            created_by=request.user,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            status='pending'
        )
        
        # Handle multiple file uploads safely
        uploaded_files = []
        if 'files' in request.FILES:
            uploaded_files.extend(request.FILES.getlist('files'))
        if 'file' in request.FILES:
            uploaded_files.extend(request.FILES.getlist('file'))
        for uploaded_file in uploaded_files:
            try:
                TodoAttachment.objects.create(
                    todo=todo,
                    file=uploaded_file,
                    original_filename=getattr(uploaded_file, 'name', 'attachment'),
                    uploaded_by=request.user
                )
            except Exception as fe:
                logger.warning(f"Error saving TodoAttachment: {fe}")
        
        return JsonResponse({
            'status': 'success',
            'todo': {
                'id': todo.id,
                'title': todo.title,
                'priority': todo.priority,
                'status': todo.status,
                'due_date': todo.due_date.isoformat() if todo.due_date else None,
                'has_attachment': todo.attachments.exists(),
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url='login')
@require_http_methods(["GET"])
def corr_todo_list_ajax(request, module_slug):
    """Fetch the list of todos for a specific module as JSON."""
    if not _can_use_todos(request.user, module_slug):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    module_info = None
    if module_slug not in ['general', 'all']:
        module = get_object_or_404(WorkModule, slug=module_slug)
        module_info = {
            'name': module.name,
            'slug': module.slug,
            'icon': getattr(module, 'icon_class', 'fas fa-folder') or 'fas fa-folder',
            'color': getattr(module, 'color', '#dc2626') or '#dc2626',
            'is_module': True
        }
        todos = Todo.objects.filter(work_module=module, created_by=request.user).order_by('-priority', '-created_at')
    elif module_slug == 'general':
        module_info = {
            'name': 'General Organizational',
            'slug': 'general',
            'icon': 'fas fa-brain',
            'color': '#dc2626',
            'is_module': False
        }
        todos = Todo.objects.filter(work_module__isnull=True, created_by=request.user).order_by('-priority', '-created_at')
    else:
        module_info = {
            'name': 'All Directives',
            'slug': 'all',
            'icon': 'fas fa-layer-group',
            'color': '#dc2626',
            'is_module': False
        }
        if request.user.role in ('manager', 'super_admin'):
            modules = WorkModule.get_visible_modules(request.user)
            todos = Todo.objects.filter(created_by=request.user).filter(Q(work_module__in=modules) | Q(work_module__isnull=True)).order_by('-priority', '-created_at')
        else:
            todos = Todo.objects.filter(created_by=request.user, work_module__isnull=True).order_by('-priority', '-created_at')
    
    todo_list = []
    for t in todos:
        todo_list.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else None,
            'is_completed': t.status == 'completed',
            'attachments': [{'id': a.id, 'name': a.original_filename, 'url': a.file.url} for a in t.attachments.all()]
        })
    
    return JsonResponse({
        'status': 'success',
        'todos': todo_list,
        'module': module_info
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def corr_todo_update(request, todo_id):
    """Update an existing module-level TODO."""
    todo = get_object_or_404(Todo, id=todo_id)
    if not _can_use_todos(request.user, todo=todo):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    try:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '')
        priority = request.POST.get('priority')
        due_date_str = request.POST.get('due_date', '')

        if title:
            todo.title = title
        if description is not None:
            todo.description = description
        if priority:
            todo.priority = priority
            
        if due_date_str:
            try:
                todo.due_date = timezone.datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except ValueError:
                pass
        elif 'due_date' in request.POST:
            todo.due_date = None

        todo.save()

        # Handle multiple file uploads on update safely
        uploaded_files = []
        if 'files' in request.FILES:
            uploaded_files.extend(request.FILES.getlist('files'))
        if 'file' in request.FILES:
            uploaded_files.extend(request.FILES.getlist('file'))
        for uploaded_file in uploaded_files:
            try:
                TodoAttachment.objects.create(
                    todo=todo,
                    file=uploaded_file,
                    original_filename=getattr(uploaded_file, 'name', 'attachment'),
                    uploaded_by=request.user
                )
            except Exception as fe:
                logger.warning(f"Error updating TodoAttachment: {fe}")

        return JsonResponse({
            'status': 'success',
            'todo': {
                'id': todo.id,
                'title': todo.title,
                'priority': todo.priority,
                'due_date': todo.due_date.isoformat() if todo.due_date else None,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url='login')
@require_http_methods(["POST"])
def corr_todo_toggle(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id)
    if not _can_use_todos(request.user, todo=todo):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    new_status = 'completed' if todo.status == 'pending' else 'pending'
    todo.status = new_status
    if new_status == 'completed':
        todo.completed_at = timezone.now()
    else:
        todo.completed_at = None
    todo.save()
    
    return JsonResponse({'status': 'success', 'new_status': todo.status})


@login_required(login_url='login')
@require_http_methods(["POST"])
def corr_todo_delete(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id)
    if not _can_use_todos(request.user, todo=todo):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    todo.delete()
    return JsonResponse({'status': 'success'})


@login_required(login_url='login')
@require_http_methods(["POST"])
def module_todo_clear(request, module_slug):
    """
    Clears all 'completed' todos for a specific module or across all modules.
    If module_slug is 'all', clears for all visible modules.
    """
    if request.user.role not in ['manager', 'super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
    if module_slug == 'all':
        # Get all modules visible to this user
        modules = WorkModule.get_visible_modules(request.user)
        todos = Todo.objects.filter(created_by=request.user).filter(Q(work_module__in=modules) | Q(work_module__isnull=True), status='completed')
    elif module_slug == 'general':
        # Clear general notes (no module)
        todos = Todo.objects.filter(work_module__isnull=True, created_by=request.user, status='completed')
    else:
        # Clear completed todos for a specific module
        todos = Todo.objects.filter(work_module__slug=module_slug, created_by=request.user, status='completed')
    
    count = todos.count()
    todos.delete()
    
    return JsonResponse({
        'status': 'success',
        'message': f'Cleared {count} completed notes.',
        'cleared_count': count
    })

def module_todo_wipe_all(request, module_slug):
    """
    Clears ALL todos for a specific module or across all modules.
    This includes both active (pending) and completed items.
    """
    if request.user.role not in ['manager', 'super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
    if module_slug == 'all':
        modules = WorkModule.get_visible_modules(request.user)
        todos = Todo.objects.filter(created_by=request.user).filter(Q(work_module__in=modules) | Q(work_module__isnull=True))
    elif module_slug == 'general':
        todos = Todo.objects.filter(work_module__isnull=True, created_by=request.user)
    else:
        todos = Todo.objects.filter(work_module__slug=module_slug, created_by=request.user)
    
    count = todos.count()
    todos.delete()
    
    return JsonResponse({
        'status': 'success',
        'message': f'Wiped all {count} notes.',
        'cleared_count': count
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def module_todo_delete_file(request, file_id):
    """Delete a specific attachment from a Todo."""
    if request.user.role not in ['manager', 'super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    attachment = get_object_or_404(TodoAttachment, id=file_id)
    todo_id = attachment.todo.id
    attachment.delete()
    
    return JsonResponse({'status': 'success', 'todo_id': todo_id})


# ============= Tasks Views =============

@login_required(login_url='login')
@require_http_methods(["GET"])
def _get_filtered_tasks(request):
    """Helper to get filtered tasks for list and export."""
    tasks = Task.objects.filter(work_module__is_archived=False).select_related('created_by', 'work_module').prefetch_related('assigned_to')
    
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    module_filter = request.GET.get('module', '')
    
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
        
    if module_filter:
        tasks = tasks.filter(work_module__slug=module_filter)
    
    if request.user.role == 'super_admin':
        pass
    elif request.user.role == 'manager':
        visible_modules = WorkModule.get_visible_modules(request.user)
        tasks = tasks.filter(
            Q(work_module__in=visible_modules) |
            Q(work_module__isnull=True, created_by=request.user) |
            Q(assigned_to=request.user) |
            Q(created_by=request.user)
        ).distinct()
    else:
        tasks = tasks.filter(
            Q(assigned_to=request.user) | 
            Q(created_by=request.user)
        ).distinct()
    
    # Premium Sorting Strategy: Priority (Critical -> High -> Med -> Low) then Deadline (Asc)
    priority_order = Case(
        When(priority='critical', then=0),
        When(priority='high', then=1),
        When(priority='medium', then=2),
        When(priority='low', then=3),
        default=4,
        output_field=IntegerField(),
    )
    
    return tasks.annotate(priority_rank=priority_order).order_by('priority_rank', 'deadline')

@login_required(login_url='login')
def task_list(request):
    """Task list view with pagination."""
    tasks_qs = _get_filtered_tasks(request)
    
    # Pagination Options
    per_page = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page)
    except (ValueError, TypeError):
        per_page = 10
        
    # Pagination
    paginator = Paginator(tasks_qs, per_page)
    page = request.GET.get('page')
    tasks = paginator.get_page(page)
    
    import time
    qs = request.GET.copy()
    qs.pop('page', None)
    module_slug = request.GET.get('module', '')
    context = {
        'wt_qs': qs.urlencode(),
        'wt_filtered': any(request.GET.get(k) for k in ('search', 'status', 'priority')),
        'wt_module_name': WorkModule.objects.filter(slug=module_slug).values_list('name', flat=True).first() if module_slug else '',
        'wt_now': timezone.now(),
        'wt_status_options': [
            ('pending', 'Not started', 'لم تبدأ'), ('in_progress', 'In progress', 'قيد التنفيذ'),
            ('submitted', 'Submitted', 'تم التسليم'), ('rejected', 'Sent back', 'أعيدت'),
            ('approved', 'Approved', 'معتمدة'), ('completed', 'Completed', 'مكتملة'), ('overdue', 'Overdue', 'متأخرة'),
        ],
        'wt_priority_options': [('critical', 'Critical', 'حرجة'), ('high', 'High', 'عالية'), ('medium', 'Medium', 'متوسطة'), ('low', 'Low', 'منخفضة')],
        'wt_per_page_options': [10, 25, 50, 100],
        'tasks': tasks,
        'tasks_count': tasks_qs.count(),
        'search': request.GET.get('search', ''),
        'status': request.GET.get('status', ''),
        'priority': request.GET.get('priority', ''),
        'module': request.GET.get('module', ''),
        'per_page': per_page,
        'now_ts': int(time.time()),
    }
    
    return render(request, 'pages/tasks_list.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def task_detail(request, task_id):
    """Task detail view."""
    task = get_object_or_404(Task, id=task_id)

    # Administrative Correspondence: Route directly to dedicated correspondence detail page
    if task.task_type == 'correspondence':
        corr_match = Correspondence.objects.filter(
            Q(reference_number=task.reference_number, reference_number__isnull=False) |
            Q(title=task.title)
        ).first()
        if not corr_match:
            corr_match = Correspondence.objects.create(
                title=task.title,
                description=task.description,
                correspondence_type=task.correspondence_type or 'memo',
                reference_number=task.reference_number,
                priority=task.priority,
                deadline=task.deadline,
                work_module=task.work_module,
                created_by=task.created_by,
                cover_image=task.cover_image,
                attachment=task.attachment,
                status='active',
            )
            corr_match.assigned_to.set(task.assigned_to.all())
        return redirect('correspondence-detail', pk=corr_match.pk)
    
    if task.work_module and task.work_module.slug == 'contact-submissions':
        if request.user.role != 'super_admin':
            messages.error(request, 'You do not have permission to view contact submission tasks.')
            return redirect('dashboard')
            
    if task.work_module and task.work_module.is_archived and request.user.role != 'super_admin':
        messages.error(request, 'This task belongs to an archived module and is no longer accessible.')
        return redirect('dashboard')

    contact_info = None
    if task.work_module and task.work_module.slug == 'contact-submissions':
        lines = task.description.split('\n')
        c_name = ""
        c_email = ""
        c_phone = ""
        c_service = ""
        c_message = ""
        
        msg_started = False
        msg_lines = []
        for line in lines:
            if msg_started:
                msg_lines.append(line)
                continue
            if line.startswith("Submission by: "):
                c_name = line.replace("Submission by: ", "").strip()
            elif line.startswith("Email: "):
                c_email = line.replace("Email: ", "").strip()
            elif line.startswith("Phone: "):
                c_phone = line.replace("Phone: ", "").strip()
            elif line.startswith("Requested Service: "):
                c_service = line.replace("Requested Service: ", "").strip()
            elif line.startswith("Message/Requirements:"):
                msg_started = True
                
        if msg_started:
            c_message = "\n".join(msg_lines).strip()
            
        contact_info = {
            'name': c_name,
            'email': c_email,
            'phone': c_phone,
            'service': c_service,
            'message': c_message,
        }

    # --- AUTO REACTIVATION CHECK ---
    # Attempt to reactivate if past due (covers for missed background tasks)
    if task.is_recurring and task.deadline and task.deadline < timezone.now():
        task.reactivate_if_needed()
        # Refresh task object if reactivated
        task.refresh_from_db()

    if request.user.role == 'worker':
        # Check if user is assigned to this task
        if not task.assigned_to.filter(id=request.user.id).exists():
            messages.error(request, 'You do not have permission to view this task.')
            return redirect('task-list')
    
    # Get existing submissions for this task
    submissions = Submission.objects.filter(task=task)
    worker_submissions = submissions.filter(worker=request.user)
    user_submission = worker_submissions.first() # latest due to ordering
    
    # Get submission status for display
    submission_status = user_submission.status if user_submission else None
    
    # Check if a new version is needed for recurring task
    needs_new_version = False
    if task.is_recurring and user_submission:
        if task.last_reactivated_at:
            if not user_submission.submitted_at or user_submission.submitted_at < task.last_reactivated_at:
                if user_submission.status != 'draft':
                    needs_new_version = True
    
    # Any user assigned to the task (worker, admin, manager) can submit
    is_assigned = task.assigned_to.filter(id=request.user.id).exists()
    is_privileged = request.user.role in ['manager', 'super_admin']
    is_correspondence = task.task_type == 'correspondence'

    # For correspondence tasks: check if user has already acknowledged
    user_acknowledged = False
    acknowledgement_roster = []
    if is_correspondence:
        ack_filter = {'task': task, 'status': 'approved'}
        if task.is_recurring and task.last_reactivated_at:
            ack_filter['submitted_at__gte'] = task.last_reactivated_at
            
        user_ack = Submission.objects.filter(worker=request.user, **ack_filter).first()
        user_acknowledged = user_ack is not None
        if is_privileged:
            # Build acknowledgement roster for managers
            assigned_users = task.assigned_to.all()
            acknowledged_ids = set(
                Submission.objects.filter(**ack_filter).values_list('worker_id', flat=True)
            )
            acknowledgement_roster = [
                {'user': u, 'acknowledged': u.id in acknowledged_ids}
                for u in assigned_users
            ]

    context = {
        'task': task,
        'contact_info': contact_info,
        'submissions': submissions if is_privileged else worker_submissions,
        'all_versions': SubmissionVersion.objects.filter(
            submission__task=task
        ).select_related('submission__worker').order_by('-created_at') if is_privileged else 
        SubmissionVersion.objects.filter(
            submission__task=task, submission__worker=request.user
        ).select_related('submission__worker').order_by('-created_at'),
        'user_submission': user_submission,
        'module_visible': task.work_module.is_visible_to(request.user, allow_archived=(request.user.role == 'super_admin')) if task.work_module else True,
        'submission_status': submission_status,
        'can_submit': is_assigned and user_submission is None and not is_correspondence,
        'is_correspondence': is_correspondence,
        'user_acknowledged': user_acknowledged,
        'can_acknowledge': is_correspondence and is_assigned and not user_acknowledged,
        'acknowledgement_roster': acknowledgement_roster,
        'ack_count': len([r for r in acknowledgement_roster if r['acknowledged']]),
        'total_assigned': task.assigned_to.count(),
        'ack_pct': int((len([r for r in acknowledgement_roster if r['acknowledged']]) / task.assigned_to.count()) * 100) if task.assigned_to.count() > 0 else 0,
        'needs_new_version': needs_new_version,
        'avg_progress': int(submissions.aggregate(Avg('progress'))['progress__avg'] or 0),
        # Submission stats for banner widgets
        'sub_approved_count': submissions.filter(status='approved').count(),
        'sub_pending_count': submissions.filter(status__in=['submitted', 'under_review']).count(),
        'sub_submitted_count': submissions.values('worker').distinct().count(),
        'sub_workers_left': max(0, task.assigned_to.count() - submissions.values('worker').distinct().count()),
        # NEW: Force Reactivation visibility
        'next_reactivation': task.next_reactivation_date,
    }

    # Build submission summary if 2+ users assigned and at least some submissions exist
    total_assigned = task.assigned_to.count()
    if is_privileged and total_assigned >= 2:
        # Get all submissions for this task
        all_subs_queryset = Submission.objects.filter(task=task).prefetch_related(
            'field_values__field', 'worker'
        ).order_by('worker__id', '-version')

        # Filter to only get the latest version for each worker
        latest_subs = {}
        for sub in all_subs_queryset:
            if sub.worker_id not in latest_subs:
                latest_subs[sub.worker_id] = sub
        
        all_subs = sorted(latest_subs.values(), key=lambda s: s.worker.get_full_name() or s.worker.email)

        if all_subs:
            has_custom_fields = task.custom_fields.exists()
            submitters = [sub.worker for sub in all_subs]

            # Build the field matrix (only when custom fields exist)
            summary_matrix = []
            if has_custom_fields:
                fields = list(task.custom_fields.all().order_by('order', 'created_at'))
                for field in fields:
                    row = {
                        'field': field,
                        'is_numeric': field.field_type == 'number',
                        'is_categorical': field.field_type in ['select', 'radio', 'checkbox', 'checkbox_group'],
                        'user_values': [],
                        'numeric_values': [],
                        'stats': {},
                    }
                    
                    # Initialize stats for categorical fields
                    if row['is_categorical']:
                        if field.field_type in ['select', 'radio', 'checkbox_group']:
                            for opt in field.options_list:
                                row['stats'][opt] = 0
                        elif field.field_type == 'checkbox':
                            row['stats'] = {'Checked': 0, 'Unchecked': 0}

                    for sub in all_subs:
                        fv = sub.field_values.filter(field=field).first()
                        val = fv.value if fv else ''
                        row['user_values'].append({
                            'user': sub.worker,
                            'value': val,
                            'submission': sub,
                        })
                        
                        if field.field_type == 'number' and val:
                            try:
                                row['numeric_values'].append(float(val))
                            except ValueError:
                                pass
                        elif row['is_categorical']:
                            if field.field_type in ['select', 'radio']:
                                if val in row['stats']:
                                    row['stats'][val] += 1
                            elif field.field_type == 'checkbox':
                                if val.lower() in ['true', 'on', '1', 'yes']:
                                    row['stats']['Checked'] += 1
                                else:
                                    row['stats']['Unchecked'] += 1
                            elif field.field_type == 'checkbox_group':
                                if val:
                                    selected_options = [o.strip() for o in val.split(',') if o.strip()]
                                    for opt in selected_options:
                                        if opt in row['stats']:
                                            row['stats'][opt] += 1
                                            
                    summary_matrix.append(row)

            context['submission_summary'] = {
                'submitters': submitters,
                'all_subs': all_subs,
                'matrix': summary_matrix,
                'has_custom_fields': has_custom_fields,
                'show': True,
            }

    # ── Admin-only TODO list ──────────────────────────────────────────────
    if request.user.role in ['super_admin', 'manager']:
        todos = task.todos.prefetch_related('attachments').all()
        context['todos'] = todos
        context['todo_pending_count'] = todos.filter(status='pending').count()
        context['todo_completed_count'] = todos.filter(status='completed').count()

    # Due line: "5 days left" / "overdue by 2 days", in both languages
    now = timezone.now()
    context['wt_now'] = now
    if task.deadline:
        secs = (task.deadline - now).total_seconds()
        late = secs < 0
        secs = abs(secs)
        days, hours = int(secs // 86400), int((secs % 86400) // 3600)
        done = task.status in ('approved', 'completed')
        if days:
            en = f"{days} day{'s' if days != 1 else ''}"
            ar = _ar_count(days, 'يوم واحد', 'يومان', 'أيام', 'يومًا')
        else:
            en = f"{hours} hour{'s' if hours != 1 else ''}"
            ar = _ar_count(hours, 'ساعة واحدة', 'ساعتان', 'ساعات', 'ساعة')
        context['wt_due'] = {
            'late': late and not done,
            'en': '' if done else (f'overdue by {en}' if late else f'{en} left'),
            'ar': '' if done else (f'التأخير: {ar}' if late else f'المتبقي: {ar}'),
        }

    return render(request, 'pages/task_detail.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_allow_resubmission(request, task_id):
    """Allow specific workers to submit a new version of a task."""
    if request.user.role not in ['manager', 'super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    task = get_object_or_404(Task, id=task_id)
    worker_ids = request.POST.getlist('worker_ids[]') # From jQuery/Fetch data
    
    if not worker_ids:
        return JsonResponse({'status': 'error', 'message': 'No workers selected'}, status=400)
    
    count = 0
    try:
        for w_id in worker_ids:
            try:
                worker = User.objects.get(id=w_id)
                if not task.assigned_to.filter(id=worker.id).exists():
                    continue
                    
                latest_sub = Submission.objects.filter(task=task, worker=worker).order_by('-version').first()
                
                # Determine next version
                new_version = 1
                if latest_sub:
                    if latest_sub.status == 'draft':
                        continue # Already has a draft version
                    new_version = latest_sub.version + 1
                
                # Update task status to show it's active again
                if task.status in ['completed', 'approved', 'rejected']:
                    task.status = 'in_progress'
                    task.save()
                    
                # Create NEW draft submission
                new_sub = Submission.objects.create(
                    task=task,
                    worker=worker,
                    version=new_version,
                    status='draft',
                    notes=f"Resubmission authorized by {request.user.get_full_name()}"
                )
                
                # Create notification
                notify_resubmission_requested(task, worker, new_sub, request.user)
                count += 1
            except (User.DoesNotExist, ValueError):
                continue
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Server error: {str(e)}'}, status=500)

    return JsonResponse({'status': 'success', 'message': f'New versions authorized for {count} workers.'})


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_start_new_version(request, task_id):
    """Explicitly start a new version/update of a submission (for recurring tasks or resubmissions)."""
    task = get_object_or_404(Task, id=task_id)
    
    # Security check
    if not task.assigned_to.filter(id=request.user.id).exists():
        messages.error(request, 'You are not assigned to this task.')
        return redirect('task-detail', task_id=task.id)
    
    # Find existing submission or create one if somehow missing
    submission = Submission.objects.filter(task=task, worker=request.user).order_by('-version').first()
    
    if submission:
        if submission.status == 'draft':
            messages.info(request, 'You already have a draft in progress.')
            return redirect('submission-edit', submission_id=submission.id)
            
        # Save a snapshot of the PREVIOUS version before incrementing
        save_submission_snapshot(submission)
        
        # Update existing submission
        submission.version += 1
        submission.status = 'draft'
        submission.notes = f"Update/Version {submission.version} started."
        submission.save()
        
        # Add a history comment for tracking
        from submissions.models import SubmissionComment
        SubmissionComment.objects.create(
            submission=submission,
            author=request.user,
            comment=f"Started new update session (v{submission.version})",
            action_type='comment',
            progress=submission.progress
        )
        
        # Save snapshot for history tracking
        save_submission_snapshot(submission)
        
        # Activity log
        ActivityLog.objects.create(
            user=request.user,
            action='update',
            object_type='Submission',
            object_id=submission.id,
            object_str=str(submission),
            description=f'Started submission update v{submission.version} for task: {task.title}'
        )
        
        messages.success(request, f'New update session (v{submission.version}) started.')
        return redirect('submission-edit', submission_id=submission.id)
    else:
        # Fallback create if none exists
        submission = Submission.objects.create(
            task=task,
            worker=request.user,
            version=1,
            status='draft',
            notes="Initial submission created."
        )
        
        ActivityLog.objects.create(
            user=request.user,
            action='create',
            object_type='Submission',
            object_id=submission.id,
            object_str=str(submission),
            description=f'Started initial submission for task: {task.title}'
        )
        
        messages.success(request, 'Initial submission session started.')
        return redirect('submission-edit', submission_id=submission.id)


@login_required(login_url='login')
@require_http_methods(["GET"])
def get_custom_fields(request, task_id):
    """AJAX endpoint to get custom fields for a task, optionally with submission values."""
    task = get_object_or_404(Task, id=task_id)
    submission_id = request.GET.get('submission_id')
    
    fields_data = []
    for field in task.custom_fields.all():
        field_info = {
            'id': field.id,
            'label': field.label,
            'field_type': field.field_type,
            'required': field.required,
            'options': field.options,
            'value': ''
        }
        
        if submission_id:
            val_obj = SubmissionFieldValue.objects.filter(submission_id=submission_id, field=field).first()
            if val_obj:
                field_info['value'] = val_obj.value
        
        fields_data.append(field_info)
        
    return JsonResponse({'fields': fields_data})


# --- NEW: MANUAL REACTIVATION ---
@login_required(login_url='login')
@require_http_methods(["POST"])
def task_reactivate(request, task_id):
    """Manually trigger a new cycle for a recurring task."""
    if request.user.role not in ['manager', 'super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
    task = get_object_or_404(Task, id=task_id)
    if not task.is_recurring:
        return JsonResponse({'status': 'error', 'message': 'This task is not recurring.'}, status=400)
        
    # Attempt reactivation (force=True moves it to the next cycle immediately)
    success = task.reactivate_if_needed(force=True)
    if success:
        messages.success(request, f'Task "{task.title}" has been successfully cycled to the next period.')
        return redirect('task-detail', task_id=task.id)
    else:
        messages.error(request, 'Failed to reactivate task. Check recurrence settings.')
        return redirect('task-detail', task_id=task.id)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def task_create(request):
    """Task create view."""
    if request.user.role == 'worker':
        messages.error(request, 'You do not have permission to create tasks.')
        return redirect('task-list')
    
    if request.method == 'POST':
        # Create task
        title = request.POST.get('title')
        description = request.POST.get('description')
        status = request.POST.get('status', 'pending')
        priority = request.POST.get('priority')
        deadline = request.POST.get('deadline')
        progress = request.POST.get('progress', 0)
        assigned_to_ids = request.POST.getlist('assigned_to')
        estimated_hours_raw = request.POST.get('estimated_hours', '0')
        kpi_weight_raw = request.POST.get('kpi_weight', '1.0')
        module_slug = request.POST.get('module')
        
        work_module = None
        if module_slug:
            work_module = WorkModule.objects.filter(slug=module_slug).first()
            
        try:
            estimated_hours = float(estimated_hours_raw) if estimated_hours_raw else 0.0
        except ValueError:
            error_msg = "Invalid numeric value for estimated hours"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'pages/task_form.html', {**_wt_task_form_choices(), 
                'users': request.user.get_teammates(),
                'modules': WorkModule.get_visible_modules(request.user),
                'initial_module': work_module,
                'initial_type': request.POST.get('task_type', 'standard')
            })
            
        try:
            kpi_weight = float(kpi_weight_raw) if kpi_weight_raw else 1.0
        except ValueError:
            error_msg = "Invalid numeric value for KPI weight"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'pages/task_form.html', {**_wt_task_form_choices(), 
                'users': request.user.get_teammates(),
                'modules': WorkModule.get_visible_modules(request.user),
                'initial_module': work_module,
                'initial_type': request.POST.get('task_type', 'standard')
            })
        
        if not all([title, priority, deadline]):
            error_msg = 'Title, priority, and deadline are required.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'pages/task_form.html', {**_wt_task_form_choices(), 
                'users': request.user.get_teammates(),
                'modules': WorkModule.get_visible_modules(request.user)
            })
        
        # Handle new task type fields
        task_type = request.POST.get('task_type', 'standard')
        correspondence_type = request.POST.get('correspondence_type') or None
        reference_number = request.POST.get('reference_number') or None
 
        # Handle recurrence fields
        is_recurring = request.POST.get('is_recurring') == 'on'
        recurrence_type = request.POST.get('recurrence_type', 'preset') if is_recurring else 'preset'
        recurrence_interval = request.POST.get('recurrence_interval') if is_recurring and recurrence_type == 'preset' else None
        recurrence_value = request.POST.get('recurrence_value') if is_recurring and recurrence_type == 'custom' else None
        recurrence_unit = request.POST.get('recurrence_unit') if is_recurring and recurrence_type == 'custom' else None
        
        recurrence_limit = -1
        if is_recurring:
            limit_forever = request.POST.get('recurrence_limit_forever') == 'on'
            if not limit_forever:
                limit_val = request.POST.get('recurrence_limit_value')
                if limit_val and limit_val.isdigit():
                    recurrence_limit = int(limit_val)
 
        # Force no recurrence for correspondence
        if task_type == 'correspondence':
            is_recurring = False
            
        # Location fields
        location_enabled = request.POST.get('location_enabled') == 'on'
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        location_name = request.POST.get('location_name')
        country = request.POST.get('country')
        wilaya = request.POST.get('wilaya')
 
        try:
            latitude = float(latitude) if latitude else None
            longitude = float(longitude) if longitude else None
        except ValueError:
            latitude = None
            longitude = None
            
        try:
            # Create task without many-to-many field
            task = Task.objects.create(
                title=title,
                description=description,
                status=status,
                priority=priority,
                work_module=work_module,
                start_date=request.POST.get('start_date') or None,
                deadline=deadline,
                progress=int(progress) if str(progress).isdigit() else 0,
                estimated_hours=estimated_hours,
                kpi_weight=kpi_weight,
                created_by=request.user,
                task_type=task_type,
                correspondence_type=correspondence_type,
                reference_number=reference_number,
                cover_image=request.FILES.get('cover_image'),
                attachment=request.FILES.get('attachment'),
                is_recurring=is_recurring,
                recurrence_type=recurrence_type,
                recurrence_interval=recurrence_interval,
                recurrence_value=int(recurrence_value) if recurrence_value and str(recurrence_value).isdigit() else None,
                recurrence_unit=recurrence_unit,
                recurrence_limit=recurrence_limit,
                last_reactivated_at=timezone.now() if is_recurring else None,
                location_enabled=location_enabled,
                latitude=latitude,
                longitude=longitude,
                location_name=location_name,
                country=country,
                wilaya=wilaya,
            )
        except PermissionDenied as e:
            raise e
        except (ValueError, Exception) as e:
            error_msg = f"Error creating task: {str(e)}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'pages/task_form.html', {**_wt_task_form_choices(), 
                'users': request.user.get_teammates(),
                'modules': WorkModule.get_visible_modules(request.user),
                'initial_module': work_module,
                'initial_type': task_type
            })
        
        # Assign workers & dispatch notifications safely
        assigned_users = User.objects.none()
        valid_assigned_ids = []
        for raw_id in assigned_to_ids:
            if isinstance(raw_id, str):
                for part in raw_id.split(','):
                    part_clean = part.strip()
                    if part_clean.isdigit():
                        valid_assigned_ids.append(int(part_clean))
            elif isinstance(raw_id, int):
                valid_assigned_ids.append(raw_id)
        if valid_assigned_ids:
            assigned_users = User.objects.filter(id__in=valid_assigned_ids, is_active=True)
            task.assigned_to.set(assigned_users)
            # Notify newly assigned workers asynchronously
            def _async_notify_workers(t_obj, workers_qs):
                for worker in workers_qs:
                    try:
                        notify_task_assigned(t_obj, worker)
                    except Exception as ne:
                        import logging
                        logging.getLogger(__name__).warning(f"Failed to notify worker {worker.id}: {ne}")

            import threading
            threading.Thread(target=_async_notify_workers, args=(task, list(assigned_users)), daemon=True).start()

        # Handle uploaded files (multiple)
        if request.FILES:
            files = request.FILES.getlist('task_files') + request.FILES.getlist('attachments[]')
            for f in files:
                Document.objects.create(
                    task=task,
                    file=f,
                    uploaded_by=request.user,
                    title=f.name,
                    original_filename=f.name,
                    file_type='task_attachment'
                )
        
        # Handle Dynamic Task Fields
        field_labels = request.POST.getlist('field_labels[]')
        field_types = request.POST.getlist('field_types[]')
        field_options = request.POST.getlist('field_options[]')
        field_indices = request.POST.getlist('field_index[]')
        field_required_indexed = request.POST.getlist('field_required_indexed[]')

        for i, label in enumerate(field_labels):
            if not label.strip():
                continue
            
            idx = field_indices[i] if i < len(field_indices) else str(i)
            is_required = idx in field_required_indexed
            
            TaskField.objects.create(
                task=task,
                label=label,
                field_type=field_types[i] if i < len(field_types) else 'text',
                options=field_options[i] if i < len(field_options) else '',
                required=is_required,
                order=i
            )

        # Notify managers/admins about the new task asynchronously
        def _async_notify_managers(t_obj, u_creator, assigned_set):
            try:
                is_corr = t_obj.task_type == 'correspondence'
                creator_name = u_creator.get_full_name() or u_creator.email
                managers = User.objects.filter(role__in=['manager', 'super_admin'], is_active=True).exclude(id=u_creator.id)
                mgr_title = f'{"Correspondence" if is_corr else "Task"} Created: {t_obj.title}'
                mgr_msg = (
                    f'{creator_name} created a new {"correspondence" if is_corr else "task"}: '
                    f'"{t_obj.title}" '
                    f'(Assigned to {len(assigned_set)} user(s)).'
                )
                for mgr in managers:
                    if mgr in assigned_set:
                        continue
                    notify(
                        recipient=mgr,
                        n_type='task_created',
                        title=mgr_title,
                        message=mgr_msg,
                        obj_type='Task',
                        obj_id=t_obj.id,
                        email_flag_name='submission_notifications',
                    )
            except Exception as me:
                import logging
                logging.getLogger(__name__).warning(f"Failed to notify managers for task {t_obj.id}: {me}")

        import threading
        threading.Thread(target=_async_notify_managers, args=(task, request.user, list(assigned_users) if valid_assigned_ids else []), daemon=True).start()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f'Task "{task.title}" created successfully.',
                'task_id': task.id,
                'redirect_url': str(reverse_lazy('task-detail', args=[task.id]))
            })

        messages.success(request, f'Task "{task.title}" created successfully.')
        return redirect('dashboard')
    
    module_slug = request.GET.get('module')
    task_type = request.GET.get('type', 'standard')
    initial_module = None
    if module_slug:
        initial_module = WorkModule.objects.filter(slug=module_slug).first()
        
    context = {
        'users': request.user.get_teammates(),
        'modules': WorkModule.get_visible_modules(request.user),
        'initial_module': initial_module,
        'initial_type': task_type,
        'recurrence_choices': Task.RECURRENCE_CHOICES,
    }
    
    return render(request, 'pages/task_form.html', {**_wt_task_form_choices(), **context})


def _wt_task_form_choices():
    """Bilingual choice lists the task form template renders (values are the model's stored values)."""
    return {
        'wt_status_options': [
            ('pending', 'Not started', 'لم تبدأ'), ('in_progress', 'In progress', 'قيد التنفيذ'),
            ('submitted', 'Submitted', 'تم التسليم'), ('rejected', 'Sent back', 'أُعيدت للتعديل'),
            ('approved', 'Approved', 'معتمدة'), ('completed', 'Completed', 'مكتملة'), ('overdue', 'Overdue', 'متأخرة'),
        ],
        'wt_priority_options': [('low', 'Low', 'منخفضة'), ('medium', 'Medium', 'متوسطة'), ('high', 'High', 'عالية'), ('critical', 'Critical', 'حرجة')],
        'wt_corr_types': [('circular', 'Circular', 'تعميم'), ('directive', 'Directive', 'توجيه'), ('memo', 'Memo', 'مذكرة'), ('notice', 'Notice', 'إشعار'), ('decision', 'Decision', 'قرار')],
        'wt_field_types': [
            ('text', 'Short text', 'نص قصير'), ('textarea', 'Long text', 'نص طويل'), ('number', 'Number', 'رقم'),
            ('select', 'Drop-down list', 'قائمة منسدلة'), ('radio', 'One choice', 'اختيار واحد'),
            ('checkbox_group', 'Several choices', 'عدة اختيارات'), ('checkbox', 'Yes / no', 'نعم / لا'),
            ('date', 'Date', 'تاريخ'), ('file', 'File upload', 'رفع ملف'), ('section', 'New section (page break)', 'قسم جديد (فاصل صفحة)'),
        ],
        'wt_units': [('minutes', 'Minutes', 'دقائق'), ('hours', 'Hours', 'ساعات'), ('days', 'Days', 'أيام'), ('weeks', 'Weeks', 'أسابيع'), ('months', 'Months', 'أشهر'), ('years', 'Years', 'سنوات')],
        'wt_people_panes': [('favorites', 'favorites-list', ''), ('workers', 'workers-list', 'worker'), ('managers', 'managers-list', 'manager'), ('admins', 'admins-list', 'super_admin')],
        'recurrence_choices': Task.RECURRENCE_CHOICES,
        'initial_type': 'standard',
    }


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def task_edit(request, task_id):
    """Task edit view."""
    task = get_object_or_404(Task, id=task_id)
    
    if request.user.role == 'worker':
        messages.error(request, 'You do not have permission to edit tasks.')
        return redirect('task-detail', task_id=task.id)
    
    if request.method == 'POST':
        try:
            task.title = request.POST.get('title', task.title)
            task.description = request.POST.get('description', task.description)
            task.status = request.POST.get('status', task.status)
            task.priority = request.POST.get('priority', task.priority)
            task.task_type = request.POST.get('task_type', task.task_type)
            task.correspondence_type = request.POST.get('correspondence_type') or None
            task.reference_number = request.POST.get('reference_number') or None
            
            if 'cover_image' in request.FILES:
                task.cover_image = request.FILES.get('cover_image')
            elif 'clear_cover_image' in request.POST:
                task.cover_image = None
                
            if 'attachment' in request.FILES:
                task.attachment = request.FILES.get('attachment')
            elif 'clear_attachment' in request.POST:
                task.attachment = None
            
            module_slug = request.POST.get('module')
            if module_slug:
                task.work_module = WorkModule.objects.filter(slug=module_slug).first()
                
            # Force no recurrence for correspondence
            if task.task_type == 'correspondence':
                task.is_recurring = False
                
            # Handle start_date - can be empty (null) or a date string
            start_date_str = request.POST.get('start_date', '')
            task.start_date = start_date_str if start_date_str else None
            task.deadline = request.POST.get('deadline', task.deadline)
            progress_val = request.POST.get('progress')
            if progress_val and str(progress_val).isdigit():
                task.progress = int(progress_val)
            task.estimated_hours = float(request.POST.get('estimated_hours', task.estimated_hours)) if request.POST.get('estimated_hours') else task.estimated_hours
            task.kpi_weight = float(request.POST.get('kpi_weight', task.kpi_weight)) if request.POST.get('kpi_weight') else task.kpi_weight
            
            # Location fields
            task.location_enabled = request.POST.get('location_enabled') == 'on'
            task.latitude = request.POST.get('latitude')
            task.longitude = request.POST.get('longitude')
            task.location_name = request.POST.get('location_name')
            task.country = request.POST.get('country')
            task.wilaya = request.POST.get('wilaya')

            try:
                task.latitude = float(task.latitude) if task.latitude else None
                task.longitude = float(task.longitude) if task.longitude else None
            except ValueError:
                task.latitude = None
                task.longitude = None
            
        except (ValueError, Exception) as e:
            error_msg = f"Error updating task values: {str(e)}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'pages/task_form.html', {**_wt_task_form_choices(), 
                'task': task,
                'users': request.user.get_teammates(),
                'modules': WorkModule.get_visible_modules(request.user),
            })
        
        assigned_to_ids = request.POST.getlist('assigned_to')
        # Capture previous assignees before updating (for notification diff)
        previous_assignee_ids = set(task.assigned_to.values_list('id', flat=True))
        # We always want to update the assigned team, even if it's empty
        valid_assigned_ids = [uid for uid in assigned_to_ids if str(uid).isdigit()]
        if valid_assigned_ids:
            assigned_users = User.objects.filter(id__in=valid_assigned_ids, is_active=True)
            task.assigned_to.set(assigned_users)
            
            # Notify newly assigned workers (those who were not assigned before)
            new_assignees = assigned_users.exclude(id__in=previous_assignee_ids)
            for worker in new_assignees:
                notify_task_assigned(task, worker)
        else:
            task.assigned_to.clear()
            
        # Handle uploaded files when editing
        if request.FILES:
            files = request.FILES.getlist('task_files')
            for f in files:
                Document.objects.create(
                    task=task,
                    file=f,
                    uploaded_by=request.user,
                    title=f.name,
                    original_filename=f.name,
                    file_type='task_attachment'
                )
        
        # Handle recurrence fields
        new_is_recurring = request.POST.get('is_recurring') == 'on'
        if not task.is_recurring and new_is_recurring:
            task.last_reactivated_at = timezone.now()
        
        task.is_recurring = new_is_recurring
        task.recurrence_type = request.POST.get('recurrence_type', 'preset') if task.is_recurring else 'preset'
        task.recurrence_interval = request.POST.get('recurrence_interval') if task.is_recurring and task.recurrence_type == 'preset' else None
        task.recurrence_value = request.POST.get('recurrence_value') if task.is_recurring and task.recurrence_type == 'custom' else None
        task.recurrence_unit = request.POST.get('recurrence_unit') if task.is_recurring and task.recurrence_type == 'custom' else None
        
        task.recurrence_limit = -1
        if task.is_recurring:
            limit_forever = request.POST.get('recurrence_limit_forever') == 'on'
            if not limit_forever:
                limit_val = request.POST.get('recurrence_limit_value')
                if limit_val and str(limit_val).isdigit():
                    task.recurrence_limit = int(limit_val)
        
        try:
            task.save()
        except Exception as e:
            error_msg = f"Error saving task: {str(e)}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'pages/task_form.html', {**_wt_task_form_choices(), 
                'task': task,
                'users': request.user.get_teammates(),
                'modules': WorkModule.get_visible_modules(request.user),
            })
        task.recalculate_progress()

        # Handle Dynamic Task Fields for Edit
        field_ids = request.POST.getlist('field_ids[]')
        field_labels = request.POST.getlist('field_labels[]')
        field_types = request.POST.getlist('field_types[]')
        field_options = request.POST.getlist('field_options[]')
        field_indices = request.POST.getlist('field_index[]')
        field_required_indexed = request.POST.getlist('field_required_indexed[]')

        existing_field_ids = list(task.custom_fields.values_list('id', flat=True))
        seen_field_ids = []

        for i, label in enumerate(field_labels):
            if not label.strip():
                continue
            
            f_id = field_ids[i] if i < len(field_ids) else 'new'
            idx = field_indices[i] if i < len(field_indices) else str(i)
            is_required = idx in field_required_indexed
            
            field_data = {
                'label': label,
                'field_type': field_types[i] if i < len(field_types) else 'text',
                'options': field_options[i] if i < len(field_options) else '',
                'required': is_required,
                'order': i
            }

            if f_id != 'new' and f_id.isdigit() and int(f_id) in existing_field_ids:
                TaskField.objects.filter(id=f_id).update(**field_data)
                seen_field_ids.append(int(f_id))
            else:
                new_field = TaskField.objects.create(task=task, **field_data)
                seen_field_ids.append(new_field.id)
        
        # Delete fields that were removed in the UI
        task.custom_fields.exclude(id__in=seen_field_ids).delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f'Task updated successfully.',
                'task_id': task.id,
                'redirect_url': reverse_lazy('task-detail', kwargs={'task_id': task.id})
            })

        messages.success(request, f'Task updated successfully.')

            # Handled by notify_task_assigned(task, worker) above for new assignees
        # ─────────────────────────────────────────────────────────────────

        return redirect('task-detail', task_id=task.id)
    
    context = {
        'task': task,
        'users': request.user.get_teammates(),
        'modules': WorkModule.get_visible_modules(request.user),
        'recurrence_choices': Task.RECURRENCE_CHOICES,
    }

    return render(request, 'pages/task_form.html', {**_wt_task_form_choices(), **context})


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_delete(request, task_id):
    """Task delete view."""
    task = get_object_or_404(Task, id=task_id)
    
    if request.user.role == 'worker':
        messages.error(request, 'You do not have permission to delete tasks.')
        return redirect('task-detail', task_id=task.id)
    
    task_title = task.title
    task.delete()
    messages.success(request, f'Task "{task_title}" deleted successfully.')
    
    # Redirect back to the page the user was on (referer) if available
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('task-list')


@login_required(login_url='login')
@require_http_methods(["POST"])
def acknowledge_task(request, task_id):
    """One-click acknowledgement for administrative correspondence tasks."""
    task = get_object_or_404(Task, id=task_id)

    if task.task_type != 'correspondence':
        messages.error(request, 'This task does not support acknowledgement.')
        return redirect('task-detail', task_id=task.id)

    if not task.assigned_to.filter(id=request.user.id).exists():
        messages.error(request, 'You are not assigned to this correspondence.')
        return redirect('task-detail', task_id=task.id)

    # Check if already acknowledged (considering recurrence)
    ack_filter = {'task': task, 'worker': request.user, 'status': 'approved'}
    if task.is_recurring and task.last_reactivated_at:
        ack_filter['submitted_at__gte'] = task.last_reactivated_at
        
    existing = Submission.objects.filter(**ack_filter).first()
    if existing:
        messages.info(request, 'You have already acknowledged this correspondence for the current cycle.')
        return redirect('task-detail', task_id=task.id)

    # Create acknowledgement submission
    submission = Submission.objects.create(
        task=task,
        worker=request.user,
        notes=f'Acknowledged receipt of {task.get_correspondence_type_display() or "correspondence"}: {task.reference_number or task.title}',
        status='approved',
        submitted_at=timezone.now(),
        version=1,
    )

    # Save dynamic field values if any were submitted
    custom_fields = task.custom_fields.all()
    for field in custom_fields:
        if field.field_type == 'checkbox_group':
            # Collect multiple checkbox values
            values = request.POST.getlist(f'field_{field.id}_multi')
            value_str = ', '.join(values) if values else ''
        elif field.field_type == 'checkbox':
            value_str = 'Yes' if request.POST.get(f'field_{field.id}') else 'No'
        else:
            value_str = request.POST.get(f'field_{field.id}', '')

        if value_str or not field.required:
            SubmissionFieldValue.objects.create(
                submission=submission,
                field=field,
                value=value_str,
            )

    # Record history
    SubmissionComment.objects.create(
        submission=submission,
        author=request.user,
        comment=f'Acknowledged by {request.user.get_full_name() or request.user.email}',
        action_type='approval',
        progress=100,
    )

    # Update task progress
    task.recalculate_progress()

    # Notify managers
    notify_correspondence_acknowledged(submission, request.user)

    messages.success(request, 'You have successfully acknowledged this correspondence.')
    return redirect('task-detail', task_id=task.id)


@login_required(login_url='login')
@require_http_methods(["POST"])
def delete_task_file(request, task_id):
    """Delete a specific task file."""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permission
    if request.user.role == 'worker':
        return JsonResponse({'success': False, 'error': 'You do not have permission to delete files.'}, status=403)
    
    file_id = request.POST.get('file_id')
    if not file_id:
        return JsonResponse({'success': False, 'error': 'File ID not provided.'}, status=400)
    
    try:
        doc = Document.objects.get(id=file_id, task=task, file_type='task_attachment')
        if doc.file:
            doc.file.delete()
        doc.delete()
        return JsonResponse({'success': True, 'message': 'File deleted successfully.'})
    except Document.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'File not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============= Submissions Views =============

@login_required(login_url='login')
@require_http_methods(["GET"])
def submission_list(request):
    """Submissions list view."""
    submissions = Submission.objects.select_related('task', 'task__work_module', 'worker', 'reviewed_by')

    # Filters
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    sort = request.GET.get('sort', '-created_at')
    if sort not in ('-created_at', 'created_at', '-updated_at', '-submitted_at'):
        sort = '-created_at'

    if search:
        submissions = submissions.filter(
            Q(task__title__icontains=search) | Q(notes__icontains=search) |
            Q(worker__first_name__icontains=search) | Q(worker__last_name__icontains=search) | Q(worker__email__icontains=search)
        )

    # Role-based visibility isolation
    if request.user.role == 'super_admin':
        pass
    elif request.user.role == 'manager':
        visible_modules = WorkModule.get_visible_modules(request.user)
        submissions = submissions.filter(
            Q(worker=request.user) | Q(task__work_module__in=visible_modules)
        ).distinct()
    else:
        submissions = submissions.filter(worker=request.user)

    counts = {
        'all': submissions.count(),
        'waiting': submissions.filter(status__in=['submitted', 'under_review']).count(),
        'approved': submissions.filter(status='approved').count(),
        'rejected': submissions.filter(status='rejected').count(),
        'draft': submissions.filter(status='draft').count(),
    }
    if status_filter == 'waiting':
        submissions = submissions.filter(status__in=['submitted', 'under_review'])
    elif status_filter in ('approved', 'rejected', 'draft'):
        submissions = submissions.filter(status=status_filter)
    else:
        status_filter = ''

    submissions = submissions.order_by(sort, '-id')
    page = Paginator(submissions, 25).get_page(request.GET.get('page'))
    qs = request.GET.copy()
    qs.pop('page', None)

    context = {
        'submissions': page,
        'wt_counts': counts,
        'wt_sl_tabs': [('', 'All', 'الكل'), ('waiting', 'Waiting for review', 'بانتظار المراجعة'), ('rejected', 'Sent back', 'أُعيدت'), ('approved', 'Approved', 'معتمدة'), ('draft', 'Drafts', 'مسودات')],
        'wt_qs': qs.urlencode(),
        'wt_filtered': bool(search or status_filter),
        'total_submissions': counts['all'],
        'pending_count': counts['waiting'],
        'approved_count': counts['approved'],
        'rejected_count': counts['rejected'],
        'is_manager': request.user.role in ['manager', 'super_admin'],
        'search': search,
        'status': status_filter,
        'sort': sort,
    }

    return render(request, 'pages/submissions_list.html', context)

def save_submission_snapshot(submission):
    """Save a snapshot of the current submission data (notes, custom fields) for history."""
    # Collect custom fields data as JSON
    field_values = SubmissionFieldValue.objects.filter(submission=submission).select_related('field')
    custom_data = {}
    for fv in field_values:
        if fv.field.field_type == 'file' and fv.file_upload:
            custom_data[fv.field.label] = f"File: {fv.file_upload.name}"
        else:
            custom_data[fv.field.label] = fv.value
        
    # Create or update the snapshot for the CURRENT version number
    version_obj, created = SubmissionVersion.objects.update_or_create(
        submission=submission,
        version_number=submission.version,
        defaults={
            'notes': submission.notes,
            'custom_fields_data': custom_data,
            'progress': submission.progress,
            'status': submission.status,
            'score': submission.score,
            'submitted_at': submission.submitted_at
        }
    )
    
    # Associate all current documents with this snapshot
    from archives.models import Document
    current_docs = Document.objects.filter(submission=submission, file_type='submission_file', version=submission.version)
    version_obj.snapshot_files.set(current_docs)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def submission_create(request):
    """Create a new submission for a task."""
    task_id = request.GET.get('task_id') or request.GET.get('task')
    task = None
    
    if task_id:
        try:
            task = Task.objects.get(id=task_id)
            # Pre-check: if they already have a submission, redirect them to the edit page immediately
            existing = Submission.objects.filter(task=task, worker=request.user).first()
            if existing:
                messages.info(request, f'You already have an active submission for "{task.title}".')
                return redirect('submission-detail', submission_id=existing.id)
        except (Task.DoesNotExist, ValueError):
            task = None
    
    if request.method == 'POST':
        post_task_id = request.POST.get('task')
        task = get_object_or_404(Task, id=post_task_id)
        
        # Check if user already has a submission for this task (double check on POST)
        existing = Submission.objects.filter(task=task, worker=request.user).first()
        if existing:
            messages.warning(request, 'You already have a submission for this task. Edit it instead.')
            return redirect('submission-detail', submission_id=existing.id)
        
        notes = request.POST.get('notes', '')
        progress_percentage = request.POST.get('progress_percentage')
        
        if progress_percentage and progress_percentage.isdigit():
            user_progress = min(max(int(progress_percentage), 0), 100)
        else:
            user_progress = 0
        
        # Submissions creation logic follows
        action = request.POST.get('action', 'draft')
        status_val = 'submitted' if action == 'submit' else 'draft'
        submitted_at_val = timezone.now() if action == 'submit' else None

        submission = Submission.objects.create(
            task=task,
            worker=request.user,
            notes=notes,
            status=status_val,
            submitted_at=submitted_at_val,
            progress=user_progress,
            version=1
        )
        
        # Recalculate collective task progress
        task.recalculate_progress()
        
        # Notification for manager of new submission is handled below after files are attached
        # if action == 'submit':
        #     notify_submission_received(submission)
        
        comment_obj = None
        if action == 'submit':
            # Create initial submission history comment
            comment_obj = SubmissionComment.objects.create(
                submission=submission,
                author=request.user,
                comment="Initial submission",
                action_type='resubmission',
                progress=task.progress
            )
            
        # Handle multiple files
        files = request.FILES.getlist('files')
        for f in files:
            Document.objects.create(
                submission=submission,
                submission_comment=comment_obj,
                file=f,
                uploaded_by=request.user,
                title=f.name,
                original_filename=f.name,
                file_type='submission_file',
                version=submission.version
            )
            
        if action == 'submit':
            # Update task status to in_progress if it was pending
            if task.status == 'pending':
                task.status = 'in_progress'
            task.save()
            
            # Create notification for managers
            notify_submission_received(submission)
            messages.success(request, 'Submission fully submitted successfully! Waiting for manager review.')
        else:
            messages.success(request, 'Submission saved as draft successfully!')

        # Handle Dynamic Custom Fields
        for field in task.custom_fields.all():
            if field.field_type == 'section':
                continue
                
            if field.field_type == 'file':
                file_obj = request.FILES.get(f'custom_field_{field.id}')
                if file_obj:
                    SubmissionFieldValue.objects.update_or_create(
                        submission=submission,
                        field=field,
                        defaults={'file_upload': file_obj, 'value': file_obj.name}
                    )
            elif field.field_type == 'checkbox_group' and request.POST.get(f'custom_field_{field.id}_is_group'):
                val_list = request.POST.getlist(f'custom_field_{field.id}')
                joined_val = ", ".join(v for v in val_list if v)
                SubmissionFieldValue.objects.update_or_create(
                    submission=submission,
                    field=field,
                    defaults={'value': joined_val}
                )
            else:
                value = request.POST.get(f'custom_field_{field.id}')
                if value is not None:
                    SubmissionFieldValue.objects.update_or_create(
                        submission=submission,
                        field=field,
                        defaults={'value': value}
                    )
        
        # Save snapshot for history tracking
        save_submission_snapshot(submission)

        return redirect('submission-detail', submission_id=submission.id)
    
    # Get available tasks for user - tasks assigned to them that they haven't submitted for yet
    # Allow users to submit independently regardless of other users' submissions (includes admin/manager)
    available_tasks = Task.objects.filter(
        assigned_to=request.user
    ).exclude(
        submissions__worker=request.user  # Only exclude if THIS user already has a submission
    ).distinct().order_by('-deadline')
    
    context = {
        'available_tasks': available_tasks,
        'selected_task': task,
    }
    
    return render(request, 'pages/submission_form.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def submission_edit(request, submission_id):
    """Edit an existing submission."""
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Check permissions - only worker who created it or managers
    is_manager = request.user.role in ['manager', 'super_admin']
    if request.user != submission.worker and not is_manager:
        messages.error(request, 'You do not have permission to edit this submission.')
        return redirect('submission-list')
    
    # Can only edit draft, submitted, or rejected submissions (Admins can edit any)
    if submission.status not in ['draft', 'submitted', 'rejected'] and not is_manager:
        messages.error(request, 'You can only edit pending submissions. Submissions that have been approved or are under review are locked.')
        return redirect('submission-detail', submission_id=submission.id)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        progress_percentage = request.POST.get('progress_percentage')
        
        # Update submission progress if provided
        if progress_percentage and progress_percentage.isdigit():
            submission.progress = min(max(int(progress_percentage), 0), 100)
            submission.save()
            # Recalculate collective task progress
            submission.task.recalculate_progress()
        
        action = request.POST.get('action', 'draft')
        
        # Determine if we should upgrade the status to submitted
        # If it's already submitted or rejected, don't revert to draft on 'Save as Draft'
        if action == 'submit' and submission.status in ['draft', 'rejected']:
            submission.status = 'submitted'
            submission.submitted_at = timezone.now()
            
            # Update task status to submitted
            submission.task.status = 'submitted'
            submission.task.save()
            
            # Create notification for managers
            notify_submission_received(submission)
            
        submission.notes = notes
        submission.save()
        
        comment_obj = None
        if action == 'submit':
            # Create resubmission history comment
            comment_obj = SubmissionComment.objects.create(
                submission=submission,
                author=request.user,
                comment="Submission resubmitted with updates",
                action_type='resubmission',
                progress=submission.task.progress
            )
        
        # Handle new multiple files
        files = request.FILES.getlist('files')
        for f in files:
            Document.objects.create(
                submission=submission,
                submission_comment=comment_obj,
                file=f,
                uploaded_by=request.user,
                title=f.name,
                original_filename=f.name,
                file_type='submission_file',
                version=submission.version
            )
            
        if action == 'submit':
            messages.success(request, 'Submission fully submitted successfully!')
        else:
            messages.success(request, 'Submission updated successfully!')

        # Handle Dynamic Custom Fields
        for field in submission.task.custom_fields.all():
            if field.field_type == 'section':
                continue
                
            if field.field_type == 'file':
                file_obj = request.FILES.get(f'custom_field_{field.id}')
                if file_obj:
                    SubmissionFieldValue.objects.update_or_create(
                        submission=submission,
                        field=field,
                        defaults={'file_upload': file_obj, 'value': file_obj.name}
                    )
            elif field.field_type == 'checkbox_group' and request.POST.get(f'custom_field_{field.id}_is_group'):
                val_list = request.POST.getlist(f'custom_field_{field.id}')
                joined_val = ", ".join(v for v in val_list if v)
                SubmissionFieldValue.objects.update_or_create(
                    submission=submission,
                    field=field,
                    defaults={'value': joined_val}
                )
            else:
                value = request.POST.get(f'custom_field_{field.id}')
                if value is not None:
                    SubmissionFieldValue.objects.update_or_create(
                        submission=submission,
                        field=field,
                        defaults={'value': value}
                    )
            
        # Save snapshot for history tracking
        save_submission_snapshot(submission)
            
        return redirect('submission-detail', submission_id=submission.id)
    
    # Only show files belonging to the CURRENT version being edited
    current_documents = Document.objects.filter(
        submission=submission,
        file_type='submission_file',
        version=submission.version
    )

    context = {
        'submission': submission,
        'current_documents': current_documents,
        'is_edit': True,
    }
    
    return render(request, 'pages/submission_form.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def submission_delete(request, submission_id):
    """Delete a submission."""
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Check permissions
    is_manager = request.user.role in ['manager', 'super_admin']
    if request.user != submission.worker and not is_manager:
        messages.error(request, 'You do not have permission to delete this submission.')
        return redirect('submission-list')
    
    # Can only delete draft submissions (Admins/Managers can delete any)
    if submission.status != 'draft' and not is_manager:
        messages.error(request, 'You can only delete draft submissions. Submitted work is locked.')
        return redirect('submission-detail', submission_id=submission.id)
    
    submission.delete()
    messages.success(request, 'Submission deleted successfully!')
    
    # Optional redirection
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('submission-list')


@login_required(login_url='login')
@require_http_methods(["GET"])
def submission_detail(request, submission_id):
    """Submission detail view."""
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Check permissions
    if submission.task.work_module and submission.task.work_module.is_archived and request.user.role != 'super_admin':
        messages.error(request, 'This submission belongs to an archived module and is no longer accessible.')
        return redirect('dashboard')

    is_manager = request.user.role in ['manager', 'super_admin']
    if request.user != submission.worker and not is_manager:
        messages.error(request, 'You do not have permission to view this submission.')
        return redirect('submission-list')
    
    # Get all submission files uploaded by the worker
    latest_submittal_files = Document.objects.filter(
        submission=submission, 
        file_type='submission_file',
        version=submission.version
    ).order_by('-uploaded_at')

    # Calculate granular task metrics for visualization
    task = submission.task
    all_assigned_users = task.assigned_to.all()
    total_workers = all_assigned_users.count()
    
    # Get all submissions for this task
    all_task_submissions = task.submissions.all()
    
    # Distinct workers with approved submissions
    approved_workers_ids = set(all_task_submissions.filter(status='approved').values_list('worker_id', flat=True))
    
    # Distinct workers with submitted/under_review submissions who haven't been approved yet
    review_workers_ids = set(all_task_submissions.filter(status__in=['submitted', 'under_review']).values_list('worker_id', flat=True))
    
    workers_approved = len(approved_workers_ids)
    workers_submitted = len([w for w in review_workers_ids if w not in approved_workers_ids])
    
    # Workers who haven't submitted anything or their submissions are rejected/draft
    workers_pending = max(0, total_workers - (workers_approved + workers_submitted))

    # Get all custom fields defined for this task
    task_fields = task.custom_fields.all().order_by('id') # or 'order' if it existed
    
    # Map values to fields (including empty ones)
    field_data = []
    submission_values = {val.field_id: val.value for val in submission.field_values.all()}
    
    for field in task_fields:
        field_data.append({
            'field': field,
            'value': submission_values.get(field.id, None)
        })
    
    custom_field_values = field_data

    context = {
        'submission': submission,
        'is_manager': is_manager,
        'latest_submittal_files': latest_submittal_files,
        'custom_field_values': custom_field_values,
        'metrics': {
            'total': total_workers,
            'approved': workers_approved,
            'submitted': workers_submitted,
            'pending': workers_pending,
            # For the pie chart CSS
            'approved_pct': int((workers_approved / total_workers * 100)) if total_workers > 0 else 0,
            'submitted_pct': int((workers_submitted / total_workers * 100)) if total_workers > 0 else 0,
            'pending_pct': int((workers_pending / total_workers * 100)) if total_workers > 0 else 0,
        }
    }
    
    return render(request, 'pages/submission_detail.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def submission_update_status(request, submission_id):
    """Update submission status."""
    submission = get_object_or_404(Submission, id=submission_id)
    
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'You do not have permission to review submissions.')
        return redirect('submission-detail', submission_id=submission.id)
    
    status = request.POST.get('status')
    manager_feedback = request.POST.get('manager_feedback', '')
    score = request.POST.get('score')
    progress_val = request.POST.get('progress')
    
    if status not in ['under_review', 'approved', 'rejected']:
        messages.error(request, 'Invalid status.')
        return redirect('submission-detail', submission_id=submission.id)
    
    submission.status = status
    submission.manager_feedback = manager_feedback
    
    # Prioritize manual progress set by the reviewer on the slider
    if progress_val and progress_val.isdigit():
        submission.progress = min(max(int(progress_val), 0), 100)
    elif status == 'approved':
        # Fallback if for some reason progress_val is missing
        submission.progress = 100
    
    # Score is out of 100, the same scale as the other KPI parts (Submission.score help text, kpi.engine)
    if score is not None and score.strip():
        try:
            submission.score = min(max(float(score), 0), 100)
        except ValueError:
            pass

    submission.reviewed_by = request.user
    submission.reviewed_at = timezone.now()
    submission.save()
    
    task = submission.task
    # Update task progress based on approvals using model-level logic
    task.recalculate_progress()
    
    # Notify worker of the review result
    notify_submission_reviewed(submission)
    
    # Save snapshot for history tracking
    save_submission_snapshot(submission)
    
    # Create a structured history comment
    action_type_val = 'approval' if status == 'approved' else 'review_request' if status == 'rejected' else 'comment'
    comment_obj = SubmissionComment.objects.create(
        submission=submission,
        author=request.user,
        comment=manager_feedback or f"Submission {status}",
        action_type=action_type_val,
        progress=submission.progress
    )
    
    review_file = request.FILES.get('review_file')
    if review_file:
        Document.objects.create(
            submission=submission,
            submission_comment=comment_obj,
            file=review_file,
            uploaded_by=request.user,
            title=review_file.name,
            original_filename=review_file.name,
            file_type='submission_comment_file'
        )
    
    if task.status == 'completed':
        messages.success(request, f'Submission {status}! All users have completed the task.')
    elif task.status == 'in_progress':
        messages.success(request, f'Submission {status} successfully. Task is in progress.')
    else:
        messages.success(request, f'Submission {status} recorded.')
    
    return redirect('submission-detail', submission_id=submission.id)


@login_required(login_url='login')
@require_http_methods(["POST"])
def submission_bulk_action(request):
    """Perform bulk actions (approve/reject) on multiple submissions."""
    if request.user.role not in ['manager', 'super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)
    
    action = request.POST.get('action')
    submission_ids = request.POST.getlist('submission_ids[]')
    
    if not submission_ids:
        return JsonResponse({'status': 'error', 'message': 'No submissions selected.'}, status=400)
    
    if action not in ['approved', 'rejected']:
        return JsonResponse({'status': 'error', 'message': 'Invalid action.'}, status=400)
    
    submissions = Submission.objects.filter(id__in=submission_ids)
    count = 0
    
    for sub in submissions:
        sub.status = action
        sub.reviewed_by = request.user
        sub.reviewed_at = timezone.now()
        sub.save()
        
        # Create comment for history
        SubmissionComment.objects.create(
            submission=sub,
            author=request.user,
            comment=f"Bulk {action} via dashboard",
            action_type='approval' if action == 'approved' else 'review_request'
        )
        
        # Recalculate task progress
        sub.task.recalculate_progress()
        
        # Notify worker
        notify_submission_reviewed(sub)
        count += 1
        
    return JsonResponse({'status': 'success', 'message': f'Successfully updated {count} submissions.'})


@login_required(login_url='login')
@require_http_methods(["POST"])
def submission_submit(request, submission_id):
    """Submit a draft submission (worker action)."""
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Check permissions - only the worker or managers can submit
    is_manager = request.user.role in ['manager', 'super_admin']
    if request.user != submission.worker and not is_manager:
        messages.error(request, 'You do not have permission to submit this.')
        return redirect('submission-detail', submission_id=submission.id)
    
    # Can only submit draft submissions
    if submission.status != 'draft':
        messages.error(request, f'Submission is already {submission.status}. You cannot submit it again.')
        return redirect('submission-detail', submission_id=submission.id)
    
    # Update submission status
    submission.status = 'submitted'
    submission.submitted_at = timezone.now()
    submission.save()
    
    # Notify manager
    notify_submission_received(submission)
    
    # Create resubmission history comment
    SubmissionComment.objects.create(
        submission=submission,
        author=request.user,
        comment="Submission submitted (Iteration)",
        action_type='resubmission'
    )
    
    # Update task status to 'submitted'
    task = submission.task
    task.status = 'submitted'
    task.recalculate_progress()
    
    # Create notification for managers
    notify_submission_received(submission)
    
    messages.success(request, 'Submission submitted successfully! Waiting for manager review.')
    return redirect('submission-detail', submission_id=submission.id)


# ============= Notifications Views =============

# Notification types: (key, English, Arabic, Font Awesome icon)
WT_NOTIF_TYPES = [
    ('task_assigned', 'Task assigned', 'مهمة مسندة', 'fa-list-check'),
    ('task_created', 'Task created', 'مهمة جديدة', 'fa-plus'),
    ('deadline_reminder', 'Deadline reminder', 'تذكير بموعد', 'fa-clock'),
    ('submission_received', 'Submission received', 'تسليم وارد', 'fa-inbox'),
    ('submission_approved', 'Submission approved', 'تسليم معتمد', 'fa-circle-check'),
    ('submission_rejected', 'Sent back', 'تسليم مُعاد', 'fa-rotate-left'),
    ('feedback_received', 'Feedback', 'ملاحظات', 'fa-comment'),
    ('correspondence_issued', 'Correspondence', 'مراسلة', 'fa-envelope-open-text'),
    ('kpi_updated', 'Score updated', 'تحديث النتيجة', 'fa-chart-line'),
]


def _notification_url(n):
    """Where a notification leads: its task, submission or correspondence (None when unknown)."""
    from django.urls import reverse, NoReverseMatch
    kind = (n.related_object_type or '').lower()
    names = {'task': 'task-detail', 'submission': 'submission-detail', 'correspondence': 'correspondence-detail'}
    if kind not in names or not n.related_object_id:
        return None
    try:
        return reverse(names[kind], args=[n.related_object_id])
    except NoReverseMatch:
        return None


@login_required(login_url='login')
@require_http_methods(["GET"])
def notifications_list(request):
    """Notifications: filter bar, then the list grouped by day, newest first, with server-side pages."""
    from django.core.paginator import Paginator

    mine = Notification.objects.filter(recipient=request.user)
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    valid_types = {t[0] for t in WT_NOTIF_TYPES}

    qs = mine
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(message__icontains=search))
    if status_filter == 'unread':
        qs = qs.filter(is_read=False)
    elif status_filter == 'read':
        qs = qs.filter(is_read=True)
    else:
        status_filter = ''
    if type_filter in valid_types:
        qs = qs.filter(notification_type=type_filter)
    else:
        type_filter = ''
    qs = qs.order_by('-created_at')

    page = Paginator(qs, 30).get_page(request.GET.get('page'))
    meta = {t[0]: t for t in WT_NOTIF_TYPES}
    today = timezone.localdate()
    groups, current = [], None
    for n in page.object_list:
        day = timezone.localtime(n.created_at).date()
        delta = (today - day).days
        if delta <= 0:
            key, en, ar = 'today', 'Today', 'اليوم'
        elif delta == 1:
            key, en, ar = 'yesterday', 'Yesterday', 'أمس'
        elif delta < 7:
            key, en, ar = 'week', 'Earlier this week', 'في وقت سابق هذا الأسبوع'
        else:
            key, en, ar = 'older', 'Older', 'أقدم'
        if current is None or current['key'] != key:
            current = {'key': key, 'en': en, 'ar': ar, 'items': []}
            groups.append(current)
        t = meta.get(n.notification_type, (n.notification_type, n.get_notification_type_display(), n.get_notification_type_display(), 'fa-bell'))
        n.wt_type_en, n.wt_type_ar, n.wt_icon = t[1], t[2], t[3]
        n.wt_url = _notification_url(n)
        n.wt_kind = n.notification_type
        current['items'].append(n)

    params = request.GET.copy()
    params.pop('page', None)
    context = {
        'page': page,
        'groups': groups,
        'total_notifications': mine.count(),
        'unread_count': mine.filter(is_read=False).count(),
        'result_count': page.paginator.count,
        'search': search,
        'status': status_filter,
        'type': type_filter,
        'wt_filtered': bool(search or status_filter or type_filter),
        'wt_qs': params.urlencode(),
        'wt_notif_types': WT_NOTIF_TYPES,
    }
    return render(request, 'pages/notifications.html', context)


def _wants_json(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@login_required(login_url='login')
@require_http_methods(["POST"])
def notification_mark_as_read(request, notification_id):
    """Mark one notification read (JSON for the page script, redirect otherwise)."""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
    if _wants_json(request):
        return JsonResponse({'status': 'success', 'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()})
    return redirect('notifications-list')


@login_required(login_url='login')
@require_http_methods(["POST"])
def notification_delete(request, notification_id):
    """Delete one notification."""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.delete()
    if _wants_json(request):
        return JsonResponse({'status': 'success', 'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()})
    messages.success(request, 'Notification deleted.')
    return redirect('notifications-list')


@login_required(login_url='login')
@require_http_methods(["POST"])
def notification_mark_all_as_read(request):
    """Mark all notifications read."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications-list')


# ============= Profile Views =============

def _say(request, en, ar):
    """Pick the message in the viewer's language (toasts are text only)."""
    from core.context_processors import _wt_lang
    return ar if _wt_lang(request) == 'ar' else en


@login_required(login_url='login')
@require_http_methods(["GET"])
def profile(request):
    """Profile: identity card, personal details, password, email notifications, recent sign-ins."""
    user = request.user
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    login_history = ActivityLog.objects.filter(user=user, action='login').order_by('-created_at')[:8]
    open_tasks = Task.objects.filter(assigned_to=user, work_module__is_archived=False).exclude(status__in=['approved', 'completed']).count()
    approved = Submission.objects.filter(worker=user, status='approved').count()
    return render(request, 'pages/profile.html', {
        'user': user,
        'profile_obj': profile_obj,
        'login_history': login_history,
        'pf_open_tasks': open_tasks,
        'pf_approved': approved,
        'pf_errors': request.session.pop('pf_errors', {}),
        'pf_section': request.session.pop('pf_section', ''),
    })


def _profile_back(request, section, errors=None):
    from django.urls import reverse
    if errors:
        request.session['pf_errors'] = errors
    request.session['pf_section'] = section
    return redirect(reverse('profile') + f'#{section}')


@login_required(login_url='login')
@require_http_methods(["POST"])
def profile_update(request):
    """Update name, position, phone and bio."""
    user = request.user
    first = (request.POST.get('first_name') or '').strip()
    last = (request.POST.get('last_name') or '').strip()
    if not first:
        return _profile_back(request, 'pf-details', {'first_name': _say(request, 'Enter your first name.', 'أدخل اسمك الأول.')})
    user.first_name, user.last_name = first[:150], last[:150]
    user.save(update_fields=['first_name', 'last_name', 'updated_at'])

    profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    profile_obj.position = (request.POST.get('position') or '').strip()[:255]
    profile_obj.phone = (request.POST.get('phone') or '').strip()[:20]
    profile_obj.bio = (request.POST.get('bio') or '').strip()[:2000]
    profile_obj.save()
    messages.success(request, _say(request, 'Profile saved.', 'تم حفظ الملف الشخصي.'))
    return _profile_back(request, 'pf-details')


@login_required(login_url='login')
@require_http_methods(["POST"])
def profile_preferences(request):
    """Email notification switches."""
    user = request.user
    user.email_notifications = 'email_notifications' in request.POST
    user.task_notifications = 'task_notifications' in request.POST
    user.submission_notifications = 'submission_notifications' in request.POST
    user.save(update_fields=['email_notifications', 'task_notifications', 'submission_notifications', 'updated_at'])
    messages.success(request, _say(request, 'Notification settings saved.', 'تم حفظ إعدادات الإشعارات.'))
    return _profile_back(request, 'pf-notify')


@login_required(login_url='login')
@require_http_methods(["POST"])
def profile_change_password(request):
    """Change password with Django's validators; keeps the current session signed in."""
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError

    user = request.user
    current = request.POST.get('current_password') or ''
    new1 = request.POST.get('new_password1') or ''
    new2 = request.POST.get('new_password2') or ''
    errors = {}
    if not user.check_password(current):
        errors['current_password'] = _say(request, 'Your current password is not correct.', 'كلمة المرور الحالية غير صحيحة.')
    elif new1 != new2:
        errors['new_password2'] = _say(request, 'The two new passwords do not match.', 'كلمتا المرور الجديدتان غير متطابقتين.')
    else:
        try:
            validate_password(new1, user)
        except ValidationError as e:
            errors['new_password1'] = _say(
                request, ' '.join(e.messages),
                'كلمة المرور ضعيفة: استخدم 8 أحرف على الأقل، وتجنّب الكلمات الشائعة والأرقام وحدها والتشابه مع اسمك أو بريدك.')
    if errors:
        return _profile_back(request, 'pf-password', errors)
    user.set_password(new1)
    user.save()
    update_session_auth_hash(request, user)
    messages.success(request, _say(request, 'Password changed.', 'تم تغيير كلمة المرور.'))
    return _profile_back(request, 'pf-password')


# ============= Admin Dashboard Views =============

@login_required(login_url='login')
@require_http_methods(["GET"])
def admin_dashboard(request):
    """Admin dashboard view."""
    if request.user.role != 'super_admin':
        messages.error(request, 'Access denied. Super Admin only.')
        return redirect('dashboard')
    
    # Get statistics
    total_users = User.objects.count()
    archived_count = WorkModule.objects.filter(is_archived=True).count()
    active_tasks = Task.objects.filter(work_module__is_archived=False).exclude(status='completed').count()
    completed_tasks = Task.objects.filter(work_module__is_archived=False, status='completed').count()
    in_progress_tasks = Task.objects.filter(work_module__is_archived=False, status='in_progress').count()
    pending_tasks = Task.objects.filter(work_module__is_archived=False, status='pending').count()
    
    # Calculate completion rate
    total_tasks = Task.objects.filter(work_module__is_archived=False).count()
    completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
    
    # Submission statistics
    all_submissions = Submission.objects.filter(task__work_module__is_archived=False)
    draft_count = all_submissions.filter(status='draft').count()
    submitted_count = all_submissions.filter(status='submitted').count()
    under_review_count = all_submissions.filter(status='under_review').count()
    approved_count = all_submissions.filter(status='approved').count()
    rejected_count = all_submissions.filter(status='rejected').count()
    total_submissions = all_submissions.count()
    
    # File tracking
    files_with_submissions = all_submissions.filter(documents__isnull=False).distinct().select_related('task', 'worker')
    total_files = files_with_submissions.count()
    avg_file_size = 0
    
    # Calculate completion percentage
    completion_percentage = round((approved_count / total_submissions * 100) if total_submissions > 0 else 0)
    
    # Get recent users
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    # Get pending reviews
    pending_reviews = Submission.objects.filter(status__in=['submitted', 'under_review']).select_related('task', 'worker')[:5]
    
    # Get recent submission files
    recent_files = files_with_submissions.order_by('-submitted_at')[:5]
    
    # User tracking and performance with pagination
    user_list = User.objects.all().select_related('department', 'profile__manager').order_by('id')
    paginator = Paginator(user_list, 10)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    recent_activity = ActivityLog.objects.all().select_related('user').order_by('-created_at')[:10]
    
    # Calculate user performance (top 5 by completion rate or total score)
    top_performers = UserKPI.objects.filter(month__month=timezone.now().month).select_related('user').order_by('-total_score')[:5]
    if not top_performers:
        # Fallback to any recent KPI if current month not calculated
        top_performers = UserKPI.objects.all().select_related('user').order_by('-total_score')[:5]

    try:
        my_today_record = AttendanceRecord.objects.filter(user=request.user, date=timezone.now().date()).first()
    except Exception:
        my_today_record = None

    context = {
        'total_users': total_users,
        'active_tasks': active_tasks,
        'pending_submissions': submitted_count + under_review_count,
        'completion_rate': completion_rate,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'pending_tasks': pending_tasks,
        'recent_users': recent_users,
        'pending_reviews': pending_reviews,
        # New submission tracking context
        'draft_count': draft_count,
        'submitted_count': submitted_count,
        'under_review_count': under_review_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_submissions': total_submissions,
        'total_files': total_files,
        'avg_file_size': 'N/A',
        'completion_percentage': completion_percentage,
        'recent_files': recent_files,
        'total_tasks': total_tasks,
        'version_snapshots_count': SubmissionVersion.objects.count(),
        'total_departments': Department.objects.count(),
        # Added for User Management focus
        'users': users,
        'recent_activity': recent_activity,
        'top_performers': top_performers,
        'role_choices': User.ROLE_CHOICES,
        'departments': Department.objects.all(),
        'now': timezone.now(),
        'month': timezone.now(),
        'potential_managers': User.objects.filter(role__in=['manager', 'super_admin']),
        'my_today_record': my_today_record, 'archived_count': WorkModule.objects.filter(is_archived=True).count(),
    }
    
    return render(request, 'pages/admin_dashboard.html', context)


def _admin_count(exclude_id=None):
    qs = User.objects.filter(role='super_admin', is_active=True)
    return qs.exclude(pk=exclude_id).count() if exclude_id else qs.count()


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def user_management(request, user_id=None):
    """Admin console > Users: one URL family for the list, the create form and the edit form."""
    from core.forms import UserAdminForm
    if request.user.role != 'super_admin':
        messages.error(request, _say(request, 'Permission denied.', 'ليست لديك صلاحية.'))
        return redirect('dashboard')

    mode = request.resolver_match.url_name
    if mode in ('user-create', 'user-edit') or user_id is not None:
        target = get_object_or_404(User, id=user_id) if user_id else None
        form = UserAdminForm(request.POST or None, request.FILES or None, instance=target, actor=request.user)
        if request.method == 'POST' and form.is_valid():
            user = form.save()
            name = user.get_full_name() or user.email
            messages.success(request, _say(request, f'{name} saved.', f'تم حفظ {name}.'))
            return redirect('user-management')
        if request.method == 'POST':
            messages.error(request, _say(request, 'Please check the highlighted fields.', 'يرجى مراجعة الحقول المحددة.'))
        # Values the page shows: what was typed after an error, else what is stored.
        plain = ['email', 'first_name', 'last_name', 'role', 'department', 'new_department', 'manager', 'position', 'phone', 'bio']
        flags = ['email_notifications', 'task_notifications', 'submission_notifications']
        if form.is_bound:
            vals = {k: form.data.get(k, '') for k in plain}
            vals.update({k: k in form.data for k in flags})
            chosen = form.data.getlist('groups')
        else:
            vals = {k: ('' if form.initial.get(k) is None else form.initial.get(k)) for k in plain}
            vals.update({k: bool(form.initial.get(k)) for k in flags})
            chosen = form.initial.get('groups', [])
        vals['department'], vals['manager'] = str(vals['department']), str(vals['manager'])
        return render(request, 'pages/create_user.html', {
            'form': form,
            'target_user': target,
            'is_edit': target is not None,
            'role_choices': User.ROLE_CHOICES,
            'departments': Department.objects.all(),
            'potential_managers': form.fields['manager'].queryset,
            'all_groups': form.fields['groups'].queryset,
            'selected_groups': [int(g) for g in chosen if str(g).isdigit()],
            'vals': vals,
            'is_me': bool(target and target.pk == request.user.pk),
        })

    users = User.objects.all().select_related('department', 'profile').order_by('-is_active', 'first_name', 'last_name', 'email')
    search = request.GET.get('search', '').strip()
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    if role_filter in dict(User.ROLE_CHOICES):
        users = users.filter(role=role_filter)
    else:
        role_filter = ''
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    else:
        status_filter = ''
    if search:
        users = users.filter(Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search)
                             | Q(department__name__icontains=search))
    from django.core.paginator import Paginator
    page = Paginator(users, 20).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    counts = dict(User.objects.values_list('role').annotate(n=Count('id')))
    return render(request, 'pages/admin_users.html', {
        'page': page,
        'result_count': page.paginator.count,
        'search': search, 'role_filter': role_filter, 'status_filter': status_filter,
        'wt_filtered': bool(search or role_filter or status_filter),
        'wt_qs': params.urlencode(),
        'role_choices': User.ROLE_CHOICES,
        'total_users': sum(counts.values()),
        'admins_count': counts.get('super_admin', 0),
        'managers_count': counts.get('manager', 0),
        'workers_count': counts.get('worker', 0),
        'inactive_count': User.objects.filter(is_active=False).count(),
        'my_id': request.user.id,
        'only_admin_id': User.objects.filter(role='super_admin', is_active=True).values_list('id', flat=True).first() if _admin_count() == 1 else None,
    })


@require_http_methods(["GET", "POST"])
def user_toggle_status(request, user_id):
    """Toggle user active/inactive status."""
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Session expired. Please log in again.'}, status=401)
        return redirect('login')

    if not (request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role in ['super_admin', 'admin'])):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        if user.is_active and user.pk == request.user.pk:
            msg = _say(request, 'You cannot deactivate your own account.', 'لا يمكنك تعطيل حسابك.')
            return JsonResponse({'status': 'error', 'message': msg}, status=400) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else (messages.error(request, msg) or redirect('user-management'))
        if user.is_active and user.role == 'super_admin' and _admin_count(user.pk) == 0:
            msg = _say(request, 'This is the only administrator.', 'هذا هو المشرف الوحيد.')
            return JsonResponse({'status': 'error', 'message': msg}, status=400) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else (messages.error(request, msg) or redirect('user-management'))
        user.is_active = not user.is_active
        user.save(update_fields=['is_active', 'updated_at'])
        status_text = "activated" if user.is_active else "deactivated"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'is_active': user.is_active,
                'email': user.email
            })
            
        messages.success(request, f'User {user.email} has been {status_text}.')
        return redirect('user-management')
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

from django.http import JsonResponse

def get_user_data(request, user_id):
    """Fetch user data for the edit modal."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthenticated'}, status=401)
    if not (request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role in ['super_admin', 'admin'])):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    data = {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
        'department_id': user.department.id if user.department else None,
        'manager_id': profile.manager.id if profile.manager else None,
    }
    return JsonResponse(data)


from django.db.models.deletion import ProtectedError
from django.db import IntegrityError, transaction

@require_http_methods(["POST", "DELETE"])
def user_delete(request, user_id):
    """Delete a user account cleanly. Super Admin / Superuser only."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'You must be logged in as an administrator to perform this action.'}, status=401)

    if not (request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role in ['super_admin', 'admin'])):
        return JsonResponse({'status': 'error', 'message': 'Permission denied. Administrator privilege required.'}, status=403)

    user = get_object_or_404(User, id=user_id)

    # Prevent self-deletion
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot delete your own account.'}, status=400)
    if user.role == 'super_admin' and user.is_active and _admin_count(user.pk) == 0:
        return JsonResponse({'status': 'error', 'message': 'This is the only administrator.'}, status=400)

    name = user.get_full_name() or user.email

    try:
        with transaction.atomic():
            user.delete()
        return JsonResponse({'status': 'success', 'message': f'User "{name}" has been permanently deleted.'})
    except (ProtectedError, IntegrityError, Exception) as e:
        # Fallback to soft deactivation to maintain database integrity (tasks, submissions, audit history)
        # Using atomic savepoint prevents TransactionManagementError on MySQL/PostgreSQL
        try:
            User.objects.filter(id=user_id).update(is_active=False)
            return JsonResponse({
                'status': 'success',
                'deactivated': True,
                'message': f'User "{name}" has linked system records (tasks, submissions, or audit logs) and cannot be hard deleted. Account has been deactivated instead.'
            })
        except Exception as err:
            return JsonResponse({
                'status': 'error',
                'message': f'Could not delete or deactivate user "{name}": {str(err)}'
            }, status=500)

@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def user_create(request):
    """Standalone page to create a new user with full options."""
    if request.user.role != 'super_admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        role = request.POST.get('role', 'worker')
        department_id = request.POST.get('department')
        new_department_name = request.POST.get('new_department_name')
        is_superuser = request.POST.get('is_superuser') == 'on'
        manager_id = request.POST.get('manager')
        
        if not email or not password:
            messages.error(request, 'Email and password are required.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'User with this email already exists.')
        else:
            try:
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    is_superuser=is_superuser,
                    is_staff=is_superuser,
                )
                if department_id:
                    user.department = Department.objects.get(id=department_id)
                    user.save()
                profile, _ = UserProfile.objects.get_or_create(user=user)
                if manager_id:
                    profile.manager = User.objects.get(id=manager_id)
                    profile.save()
                messages.success(request, f'User "{first_name} {last_name}" created successfully.')
                return redirect('user-management')
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
    
    context = {
        'role_choices': User.ROLE_CHOICES,
        'departments': Department.objects.all(),
        'potential_managers': User.objects.filter(role__in=['manager', 'super_admin']),
    }
    return render(request, 'pages/create_user.html', context)
    
    return redirect('user-management')


@login_required(login_url='login')
@require_http_methods(["GET"])
def kpi_dashboard(request):
    """KPI and performance dashboard."""
    if request.user.role == 'worker':
        # Workers see only their own KPI
        from kpi.models import UserKPI
        kpi_records = UserKPI.objects.filter(user=request.user).order_by('-month')[:12]
        
        context = {
            'kpi_records': kpi_records,
            'current_month': kpi_records.first() if kpi_records else None,
        }
    else:
        # Managers/Admins see all KPIs
        from kpi.models import UserKPI
        from django.db.models import Avg
        
        all_kpi = UserKPI.objects.filter(
            month__gte=timezone.now().date().replace(day=1) - datetime.timedelta(days=90)
        )
        
        kpi_stats = all_kpi.aggregate(
            avg_completion=Avg('completion_rate'),
            avg_quality=Avg('quality_score'),
            avg_on_time=Avg('on_time_rate'),
        )
        
        top_performers = UserKPI.objects.filter(
            month=timezone.now().date().replace(day=1)
        ).order_by('-total_score')[:5]
        
        
        # We need to serialize the data for Chart.js
        all_kpi_json = list(all_kpi.values('completion_rate', 'quality_score', 'on_time_rate', 'total_score', 'month'))
        for item in all_kpi_json:
            item['month'] = item['month'].strftime('%Y-%m-%d')
            
        context = {
            'all_kpi': all_kpi,
            'all_kpi_json': json.dumps(all_kpi_json),
            'kpi_stats': kpi_stats,
            'top_performers': top_performers,
        }
    
    return render(request, 'pages/kpi_dashboard.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def audit_logs(request):
    """View system activity logs."""
    if request.user.role not in ['super_admin', 'manager']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    from audit.models import ActivityLog
    
    logs = ActivityLog.objects.all()
    
    # Filters
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    object_type_filter = request.GET.get('object_type', '')
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    
    if object_type_filter:
        logs = logs.filter(object_type=object_type_filter)
    
    logs = logs.order_by('-created_at')
    
    context = {
        'logs': logs[:500],  # Limit to last 500
        'action_choices': ActivityLog.ACTION_TYPES,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'object_type_filter': object_type_filter,
    }
    
    return render(request, 'pages/audit_logs.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def admin_settings(request):
    """System settings management."""
    if request.user.role != 'super_admin':
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    settings = SiteSettings.get_settings()
    
    if request.method == 'POST':
        allow_registration = request.POST.get('allow_registration') == 'on'
        force_language_reload = request.POST.get('force_language_reload') == 'on'
        print(f"[DEBUG] admin_settings POST. allow_reg: {allow_registration}, force_reload: {force_language_reload}", flush=True)
        default_language = request.POST.get('default_language', 'ar')
        if default_language not in ['ar', 'en']:
            default_language = 'ar'
        settings.allow_registration = allow_registration
        settings.force_language_reload = force_language_reload
        settings.default_language = default_language
        settings.save()
        request.session['django_language'] = default_language
        messages.success(request, 'Settings updated successfully.')
        resp = redirect('admin-settings')
        resp.set_cookie('django_language', default_language, max_age=365*24*60*60, path='/')
        resp.set_cookie('worktrack_lang', default_language, max_age=365*24*60*60, path='/')
        return resp
        
    context = {
        'settings': settings,
    }
    return render(request, 'pages/admin_settings.html', context)


# ============= Error Handlers =============

def handler_404(request, exception):
    """Handle 404 errors."""
    return render(request, '404.html', status=404)


def handler_500(request):
    """Handle 500 errors."""
    return render(request, '500.html', status=500)


@require_http_methods(["GET", "POST"])
def register_new_user(request):
    """Unified user creation: redirects to the single canonical user management creation page."""
    return redirect('user-create')


# ============= Manager Portal Views =============

@login_required(login_url='login')
@require_http_methods(["GET"])
def manager_portal(request):
    """Dedicated Manager Portal - Team Management"""
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'You do not have access to the manager portal.')
        return redirect('dashboard')
    
    # Get manager's team
    team_members = User.objects.filter(
        profile__manager=request.user,
        is_active=True
    ).select_related('department', 'profile__manager')
    
    # Team statistics
    team_stats = {
        'total_members': team_members.count(),
        'active_members': team_members.filter(is_active=True).count(),
    }
    
    # Tasks assigned to team members
    all_team_tasks = Task.objects.filter(
        assigned_to__in=team_members,
        work_module__is_archived=False
    ).select_related('created_by', 'work_module')
    team_standard = all_team_tasks.filter(task_type='standard')
    # Correspondence for team — use the new Correspondence model
    team_corr_qs = Correspondence.objects.filter(
        assigned_to__in=team_members, 
        status='active',
        work_module__is_archived=False
    )
    corr_stats = {
        'total': team_corr_qs.count(),
        'pending': team_corr_qs.filter(status='active').count(),
        'completed': team_corr_qs.filter(status='archived').count(),
    }

    # Recent correspondence from Correspondence model
    recent_correspondence = team_corr_qs.select_related('created_by', 'work_module').order_by('-created_at')[:8]

    # Team standard task stats
    tasks_stats = {
        'total': team_standard.count(),
        'pending': team_standard.filter(status='pending').count(),
        'in_progress': team_standard.filter(status='in_progress').count(),
        'completed': team_standard.filter(status__in=['completed', 'approved']).count(),
    }

    # Recent standard tasks
    recent_tasks = team_standard.order_by('-created_at')[:8]

    # Submissions from team
    team_submissions_qs = Submission.objects.filter(
        worker__in=team_members,
        task__work_module__is_archived=False
    )
    pending_submissions = team_submissions_qs.filter(
        status='submitted'
    ).select_related('task', 'worker')

    submissions_stats = {
        'total': team_submissions_qs.count(),
        'submitted': pending_submissions.count(),
        'approved': team_submissions_qs.filter(status='approved').count(),
        'rejected': team_submissions_qs.filter(status='rejected').count(),
    }

    try:
        my_today_record = AttendanceRecord.objects.filter(user=request.user, date=timezone.now().date()).first()
    except Exception:
        my_today_record = None

    # Fetch Manager Modules with rich stats matching Admin Dashboard
    selected_group = request.GET.get('group', 'all')
    mod_data = get_module_workspace_stats(request.user, selected_group)

    # Fetch Available Modules for Explore option
    enrolled_task_module_ids = Task.objects.filter(assigned_to=request.user).values_list('work_module_id', flat=True).distinct()
    enrolled_users_ids = request.user.enrolled_modules.values_list('id', flat=True)
    all_enrolled_ids = set(list(enrolled_task_module_ids) + list(enrolled_users_ids))
    available_modules = WorkModule.objects.filter(allow_enrollment=True, is_archived=False).exclude(id__in=all_enrolled_ids).order_by('-created_at')

    completion_rate = round((tasks_stats['completed'] / tasks_stats['total'] * 100) if tasks_stats['total'] > 0 else 0)

    module_stats = mod_data['module_stats']
    average_module_progress = 0
    average_module_completion = 0
    if module_stats:
        active_progress_sum = sum(m['progress'] for m in module_stats if m['progress'] is not None)
        average_module_progress = round(active_progress_sum / len(module_stats))
        active_rate_sum = sum(m['rate'] for m in module_stats if m['rate'] is not None)
        average_module_completion = round(active_rate_sum / len(module_stats))

    context = {
        'team_members': team_members,
        'team_stats': team_stats,
        'tasks_stats': tasks_stats,
        'corr_stats': corr_stats,
        'team_tasks': team_standard,
        'recent_tasks': recent_tasks,
        'recent_correspondence': recent_correspondence,
        'pending_submissions': pending_submissions,
        'pending_count': pending_submissions.count(),
        'submissions_stats': submissions_stats,
        'total_submissions': submissions_stats['total'],
        'submissions_count': submissions_stats['total'],
        'my_today_record': my_today_record,
        'manager_modules': mod_data['modules_list'],
        'available_modules': available_modules,
        'completion_rate': completion_rate,
        'average_module_progress': average_module_progress,
        'average_module_completion': average_module_completion,
        'total_tasks': tasks_stats['total'],
        'total_corr': corr_stats['total'],
        # Module display context matching Admin Dashboard
        'modules_list': mod_data['modules_list'],
        'module_stats_list': mod_data['module_stats'],
        'module_count': mod_data['module_count'],
        'available_groups': mod_data['available_groups'],
        'selected_group': mod_data['selected_group'],
        'group_progress': mod_data['group_progress'],
        'is_manager': True,
    }
    return render(request, 'pages/manager_portal.html', context)


# ============= Worker Portal Views =============

@login_required(login_url='login')
@require_http_methods(["GET"])
def worker_portal(request):
    """Dedicated Worker Portal - Task & Submission Management"""
    if request.user.role not in ('worker', 'super_admin', 'manager'):
        messages.error(request, 'You do not have access to the worker portal.')
        return redirect('dashboard')
    
    # Get user's tasks (only their assigned tasks)
    all_my_tasks = Task.objects.filter(
        assigned_to=request.user,
        work_module__is_archived=False
    ).select_related('created_by', 'work_module')
    my_tasks = all_my_tasks.filter(task_type='standard')
    # Correspondence from the new Correspondence model where worker is assigned
    my_corr_qs = Correspondence.objects.filter(
        assigned_to=request.user, 
        status='active',
        work_module__is_archived=False
    )
    
    # Task statistics (standard tasks only)
    tasks_stats = {
        'total': my_tasks.count(),
        'pending': my_tasks.filter(status='pending').count(),
        'in_progress': my_tasks.filter(status='in_progress').count(),
        'completed': my_tasks.filter(status__in=['approved', 'completed']).count(),
    }
    
    # Get user's submissions (standard tasks only)
    my_submissions = Submission.objects.filter(
        worker=request.user, 
        task__task_type='standard',
        task__work_module__is_archived=False
    ).select_related('task', 'task__work_module', 'reviewed_by')
    
    submissions_stats = {
        'total': my_submissions.count(),
        'draft': my_submissions.filter(status='draft').count(),
        'submitted': my_submissions.filter(status='submitted').count(),
        'under_review': my_submissions.filter(status='under_review').count(),
        'approved': my_submissions.filter(status='approved').count(),
        'rejected': my_submissions.filter(status='rejected').count(),
    }
    
    # Recent tasks
    recent_tasks = my_tasks.order_by('-created_at')[:5]
    
    # Recent submissions
    recent_submissions = my_submissions.order_by('-created_at')[:5]
    
    # Pending tasks (need action, no slice)
    # Include 'rejected', 'overdue', and 'submitted' to ensure full visibility
    potential_pending = my_tasks.filter(status__in=['pending', 'in_progress', 'rejected', 'overdue', 'submitted'])
    
    # Refine: Exclude tasks where this specific worker already has an approved submission for the current cycle.
    # This is crucial for multi-worker tasks where the overall task status remains 'in_progress' or 'submitted'
    # even after one worker is approved.
    exclude_ids = []
    # 1. Non-recurring tasks
    exclude_ids.extend(Submission.objects.filter(
        worker=request.user, 
        status='approved',
        task__is_recurring=False
    ).values_list('task_id', flat=True))
    
    # 2. Recurring tasks (must check current cycle)
    recurring_assigned = my_tasks.filter(is_recurring=True)
    for rt in recurring_assigned:
        since = rt.last_reactivated_at if rt.last_reactivated_at else rt.created_at
        if Submission.objects.filter(task=rt, worker=request.user, status='approved', created_at__gte=since).exists():
            exclude_ids.append(rt.id)
            
    pending_tasks = potential_pending.exclude(id__in=exclude_ids).order_by('deadline')
    
    # Calculate real completed tasks and overall completion for the worker
    completed_task_ids = set(my_tasks.filter(status__in=['approved', 'completed']).values_list('id', flat=True))
    completed_task_ids.update(exclude_ids)
    completed_tasks_count = len(completed_task_ids)
    tasks_stats['completed'] = completed_tasks_count

    if tasks_stats['total'] > 0:
        overall_completion = round((completed_tasks_count / tasks_stats['total']) * 100)
    else:
        overall_completion = 0

    # Rejected submissions that need action
    # Only tasks whose latest submission from this worker was sent back (one row per task)
    from django.db.models import OuterRef, Subquery
    latest_sub_id = Submission.objects.filter(worker=request.user, task=OuterRef('task')).order_by('-created_at', '-id').values('id')[:1]
    rejected_submissions = my_submissions.filter(status='rejected').annotate(latest_id=Subquery(latest_sub_id)).filter(id=F('latest_id')).order_by('-reviewed_at')

    # Build correspondence list with acknowledgement info using new Correspondence model
    my_correspondence = []
    pending_correspondence_count = 0
    for c in my_corr_qs.order_by('-created_at'):
        user_acked = c.acknowledgements.filter(user=request.user).exists()
        my_correspondence.append({
            'obj': c,
            'correspondence': c,
            'id': c.id,
            'reference_number': c.reference_number,
            'title': c.title,
            'correspondence_type': c.correspondence_type,
            'priority': c.priority,
            'deadline': c.deadline,
            'cover_image': c.cover_image,
            'detail_url': f'/correspondence/{c.pk}/',
            'acknowledged': user_acked,
            'status': 'read' if user_acked else 'unread',
            'get_status_display': 'Read' if user_acked else 'Unread',
        })
        if not user_acked:
            pending_correspondence_count += 1

    corr_stats = {
        'total': my_corr_qs.count(),
        'pending': pending_correspondence_count,
        'completed': my_corr_qs.count() - pending_correspondence_count,
    }

    assigned_module_ids = set(Task.objects.filter(assigned_to=request.user).values_list('work_module', flat=True).distinct())
    shared_module_ids = set(WorkModule.objects.filter(is_shared=True, is_archived=False).values_list('id', flat=True))
    enrolled_users_ids = set(request.user.enrolled_modules.filter(is_archived=False).values_list('id', flat=True))
    
    # A module is shown in "My Modules" if:
    # 1. It is shared AND the user has tasks assigned to them OR
    # 2. The user has explicitly enrolled in it.
    worker_module_ids = list(assigned_module_ids.intersection(shared_module_ids).union(enrolled_users_ids))
    worker_modules = []
    
    from django.db.models import Prefetch
    
    # Prefetch only tasks assigned to THIS worker for each module
    modules_with_tasks = WorkModule.objects.filter(
        id__in=worker_module_ids,
        is_archived=False
    ).prefetch_related(
        Prefetch(
            'tasks',
            queryset=Task.objects.filter(assigned_to=request.user).order_by('-created_at'),
            to_attr='my_module_tasks'
        )
    )
    for wm in modules_with_tasks:
        tasks_in_module = wm.my_module_tasks
        total = len(tasks_in_module)
        
        # Personalized completion check
        completed = 0
        for t in tasks_in_module:
            if t.status in ['completed', 'approved']:
                completed += 1
                continue
            
            # Check if this specific worker is already approved for this task/cycle
            since = t.last_reactivated_at if (t.is_recurring and t.last_reactivated_at) else None
            user_approved = Submission.objects.filter(task=t, worker=request.user, status='approved')
            if since:
                user_approved = user_approved.filter(created_at__gte=since)
                
            if user_approved.exists():
                completed += 1
                
        pending = total - completed
        rate = round((completed / total) * 100) if total > 0 else 0
        
        worker_modules.append({
            'obj': wm,
            'tasks': tasks_in_module,
            'total': total,
            'completed': completed,
            'pending': pending,
            'rate': rate
        })

    try:
        my_today_record = AttendanceRecord.objects.filter(user=request.user, date=timezone.now().date()).first()
    except Exception:
        my_today_record = None

    # Fetch Available Modules for Explore tab
    enrolled_worker_module_ids = Task.objects.filter(assigned_to=request.user).values_list('work_module_id', flat=True).distinct()
    enrolled_users_ids2 = request.user.enrolled_modules.values_list('id', flat=True)
    all_enrolled_ids = set(list(enrolled_worker_module_ids) + list(enrolled_users_ids2))
    available_modules = WorkModule.objects.filter(allow_enrollment=True, is_archived=False).exclude(id__in=all_enrolled_ids).annotate(task_count=Count('tasks')).order_by('-created_at')

    # Worker home (read-only): open tasks grouped by when they are due, unread circulars first
    now = timezone.now()
    week_end = now + datetime.timedelta(days=7)
    up = {'overdue': [], 'week': [], 'later': [], 'waiting': []}
    for t in pending_tasks.select_related('work_module'):
        if t.status == 'submitted':
            up['waiting'].append(t)
        elif t.deadline and t.deadline < now:
            up['overdue'].append(t)
        elif t.deadline and t.deadline <= week_end:
            up['week'].append(t)
        else:
            up['later'].append(t)
    wt_up_groups = [
        {'key': 'overdue', 'en': 'Overdue', 'ar': 'متأخرة', 'tasks': up['overdue']},
        {'key': 'week', 'en': 'Next 7 days', 'ar': 'خلال الأيام السبعة القادمة', 'tasks': up['week']},
        {'key': 'later', 'en': 'Later', 'ar': 'لاحقًا', 'tasks': up['later']},
        {'key': 'waiting', 'en': 'Waiting for review', 'ar': 'بانتظار المراجعة', 'tasks': up['waiting']},
    ]
    hour = timezone.localtime(now).hour
    for t in up['week']:
        t.wt_due_ar = _ar_date(t.deadline)
    n_week, n_late = len(up['week']), len(up['overdue'])
    head_ar = (_ar_count(n_week, 'مهمة واحدة مستحقة', 'مهمتان مستحقتان', 'مهام مستحقة', 'مهمة مستحقة') + ' خلال الأيام السبعة القادمة') if n_week else 'لا مهام مستحقة خلال الأيام السبعة القادمة'
    if n_late:
        head_ar += '، و' + _ar_count(n_late, 'مهمة واحدة متأخرة', 'مهمتان متأخرتان', 'مهام متأخرة', 'مهمة متأخرة')

    context = {
        'wt_today_ar': _ar_date(timezone.localdate()),
        'wt_head_ar': head_ar,
        'wt_up_groups': wt_up_groups,
        'wt_up_open': len(up['overdue']) + len(up['week']) + len(up['later']),
        'wt_up_overdue': len(up['overdue']),
        'wt_up_week': len(up['week']),
        'wt_greeting': 'morning' if hour < 12 else ('afternoon' if hour < 18 else 'evening'),
        'wt_today_date': timezone.localdate(),
        'wt_circulars': sorted(my_correspondence, key=lambda r: r['acknowledged'])[:5],
        'wt_waiting_review': submissions_stats['submitted'] + submissions_stats['under_review'],
        'my_tasks': my_tasks,
        'tasks_stats': tasks_stats,
        'corr_stats': corr_stats,
        'my_submissions': my_submissions,
        'submissions_stats': submissions_stats,
        'recent_tasks': recent_tasks,
        'recent_submissions': recent_submissions,
        'pending_tasks': pending_tasks,
        'rejected_submissions': rejected_submissions,
        'my_correspondence': my_correspondence,
        'correspondence_count': corr_stats['total'],
        'pending_correspondence_count': corr_stats['pending'],
        'my_today_record': my_today_record,
        'worker_modules': worker_modules,
        'overall_completion': overall_completion,
        'available_modules': available_modules,
    }
    return render(request, 'pages/worker_portal.html', context)


# ═══════════════════════════════════════════════════════
# NEW IMPROVEMENTS — Added automatically
# ═══════════════════════════════════════════════════════
import json
import csv
import datetime as _dt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F as _F
from tasks.models import TaskComment


# ── Improvement #4: Notification live-poll count ──────

@login_required(login_url='login')
def notifications_unread_count(request):
    """Return JSON with current unread notification count. Used by navbar bell poller."""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread': count})


# ── Improvement #3: Task Comment (Discussion Thread) ──

@login_required(login_url='login')
@require_http_methods(["POST"])
def task_comment_add(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user != task.created_by and request.user not in task.assigned_to.all():
        if request.user.role not in ['manager', 'super_admin']:
            return JsonResponse({'error': 'Permission denied'}, status=403)
    message_text = request.POST.get('message', '').strip()
    if not message_text:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)
    comment = TaskComment.objects.create(
        task=task,
        author=request.user,
        message=message_text,
    )
    
    attachment = request.FILES.get('attachment')
    doc = None
    if attachment:
        doc = Document.objects.create(
            task=task,
            task_comment=comment,
            file=attachment,
            uploaded_by=request.user,
            title=attachment.name,
            original_filename=attachment.name,
            file_type='task_comment_file'
        )

    notify_task_comment(comment)
    return JsonResponse({
        'id': comment.id,
        'author': comment.author.get_full_name() or comment.author.email,
        'author_initials': ((comment.author.first_name[:1] + comment.author.last_name[:1]).upper()
                            or comment.author.email[:2].upper()),
        'message': comment.message,
        'created_at': comment.created_at.strftime('%b %d, %Y %H:%M'),
        'has_attachment': doc is not None,
        'attachment_url': doc.file.url if doc else '',
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_comment_delete(request, comment_id):
    comment = get_object_or_404(TaskComment, id=comment_id)
    if comment.author != request.user and request.user.role not in ['manager', 'super_admin']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    comment.delete()
    return JsonResponse({'success': True})


# ── Admin TODO Management ─────────────────────────────────────────────────

def _is_admin(user):
    """Quick check for admin-level roles."""
    return user.role in ['super_admin', 'manager']


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_todo_add(request, task_id):
    """Create a new TODO item on a task (admin-only)."""
    if not _is_admin(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    task = get_object_or_404(Task, id=task_id)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)
    todo = TaskTodo.objects.create(
        task=task,
        created_by=request.user,
        title=title,
        description=request.POST.get('description', '').strip(),
        priority=request.POST.get('priority', 'medium'),
    )
    # Handle any files uploaded alongside the todo
    for f in request.FILES.getlist('files'):
        TaskTodoAttachment.objects.create(
            todo=todo,
            file=f,
            original_filename=f.name,
            uploaded_by=request.user,
        )
    return JsonResponse({
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'status': todo.status,
        'priority': todo.priority,
        'created_at': todo.created_at.strftime('%b %d, %Y %H:%M'),
        'attachments': [
            {'id': a.id, 'name': a.original_filename, 'url': a.file.url}
            for a in todo.attachments.all()
        ],
    }, status=201)


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_todo_update(request, todo_id):
    """Edit a TODO item (admin-only)."""
    if not _is_admin(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    todo = get_object_or_404(TaskTodo, id=todo_id)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)
    todo.title = title
    todo.description = request.POST.get('description', '').strip()
    todo.priority = request.POST.get('priority', todo.priority)
    todo.save()
    return JsonResponse({
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'priority': todo.priority,
        'updated_at': todo.updated_at.strftime('%b %d, %Y %H:%M'),
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_todo_toggle(request, todo_id):
    """Toggle a TODO item between pending and completed (admin-only)."""
    if not _is_admin(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    todo = get_object_or_404(TaskTodo, id=todo_id)
    if todo.status == 'pending':
        todo.status = 'completed'
        todo.completed_at = timezone.now()
    else:
        todo.status = 'pending'
        todo.completed_at = None
    todo.save()
    return JsonResponse({
        'id': todo.id,
        'status': todo.status,
        'completed_at': todo.completed_at.strftime('%b %d, %Y %H:%M') if todo.completed_at else None,
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_todo_delete(request, todo_id):
    """Delete a TODO item (admin-only)."""
    if not _is_admin(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    todo = get_object_or_404(TaskTodo, id=todo_id)
    todo.delete()
    return JsonResponse({'success': True})


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_todo_upload(request, todo_id):
    """Upload files to a TODO item (admin-only)."""
    if not _is_admin(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    todo = get_object_or_404(TaskTodo, id=todo_id)
    files = request.FILES.getlist('files')
    if not files:
        return JsonResponse({'error': 'No files provided'}, status=400)
    created = []
    for f in files:
        att = TaskTodoAttachment.objects.create(
            todo=todo,
            file=f,
            original_filename=f.name,
            uploaded_by=request.user,
        )
        created.append({'id': att.id, 'name': att.original_filename, 'url': att.file.url})
    return JsonResponse({'attachments': created}, status=201)


@login_required(login_url='login')
@require_http_methods(["POST"])
def task_todo_delete_file(request, file_id):
    """Delete an attachment from a TODO item (admin-only)."""
    if not _is_admin(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    att = get_object_or_404(TaskTodoAttachment, id=file_id)
    att.file.delete(save=False)
    att.delete()
    return JsonResponse({'success': True})


# ── Improvement #11: Global Search ────────────────────

@login_required(login_url='login')
def global_search(request):
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse({'tasks': [], 'users': [], 'modules': []})
    task_qs = Task.objects.filter(
        Q(title__icontains=q) | Q(description__icontains=q) | Q(reference_number__icontains=q)
    )
    if request.user.role == 'worker':
        task_qs = task_qs.filter(assigned_to=request.user)
    tasks = [{'id': t.id, 'title': t.title, 'status': t.status, 'url': f'/tasks/{t.id}/'} for t in task_qs[:8]]
    users = []
    if request.user.role in ['manager', 'super_admin']:
        user_qs = User.objects.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
        )[:6]
        users = [{'id': u.id, 'name': u.get_full_name() or u.email, 'role': u.get_role_display(), 'email': u.email} for u in user_qs]
    module_qs = WorkModule.objects.filter(
        Q(name__icontains=q) | Q(description__icontains=q),
        is_archived=False
    )[:5]
    modules = [{'id': m.id, 'name': m.name, 'url': f'/module/{m.slug}/'} for m in module_qs]
    return JsonResponse({'tasks': tasks, 'users': users, 'modules': modules})


# ── Improvement #7: CSV Export ────────────────────────

@login_required(login_url='login')
def export_tasks_csv(request):
    import csv
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tasks_export.csv"'
    w = csv.writer(response)
    w.writerow(['ID','Title','Module','Status','Priority','Assigned To','Deadline','Progress %','Created By','Created At'])
    
    # Use the same filtering logic
    qs = _get_filtered_tasks(request)
    for t in qs:
        assigned = ', '.join(u.get_full_name() or u.email for u in t.assigned_to.all())
        w.writerow([t.id, t.title, t.work_module.name if t.work_module else t.module,
                    t.get_status_display(), t.get_priority_display(), assigned,
                    t.deadline.strftime('%Y-%m-%d %H:%M') if t.deadline else '',
                    t.progress, t.created_by.get_full_name() or t.created_by.email,
                    t.created_at.strftime('%Y-%m-%d')])
    return response


@login_required(login_url='login')
def export_submissions_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="submissions_export.csv"'
    w = csv.writer(response)
    w.writerow(['ID','Task','Worker','Status','Score','Version','Submitted At','Reviewed By','Reviewed At','Feedback'])
    qs = (Submission.objects.select_related('task','worker','reviewed_by')
          if request.user.role in ['manager','super_admin']
          else Submission.objects.filter(worker=request.user).select_related('task','worker','reviewed_by'))
    for s in qs:
        w.writerow([s.id, s.task.title, s.worker.get_full_name() or s.worker.email,
                    s.get_status_display(), s.score if s.score is not None else '', s.version,
                    s.submitted_at.strftime('%Y-%m-%d %H:%M') if s.submitted_at else '',
                    s.reviewed_by.get_full_name() if s.reviewed_by else '',
                    s.reviewed_at.strftime('%Y-%m-%d %H:%M') if s.reviewed_at else '',
                    s.manager_feedback])
    return response


# ── Improvement #5: Worker Performance Page ───────────


@login_required(login_url='login')
def export_performance_report_csv(request):
    import csv
    from django.http import HttpResponse
    from attendance.models import AttendanceRecord
    
    req_user_id = request.GET.get('user_id')
    target_user = request.user
    if req_user_id and request.user.role in ['manager', 'super_admin']:
        target_user = get_object_or_404(User, id=req_user_id)
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="performance_report_{target_user.id}.csv"'
    w = csv.writer(response)
    
    # Basic Info
    w.writerow(['Performance Report for:', target_user.get_full_name() or target_user.email])
    w.writerow(['Role:', target_user.get_role_display()])
    w.writerow(['Date Exported:', timezone.now().strftime('%Y-%m-%d %H:%M')])
    w.writerow([])
    
    # Tasks Overview
    w.writerow(['--- TASK METRICS ---'])
    assigned = Task.objects.filter(assigned_to=target_user, work_module__is_archived=False)
    total_tasks = assigned.count()
    completed_tasks = assigned.filter(status__in=['approved','completed']).count()
    overdue_tasks = assigned.filter(status='overdue').count()
    w.writerow(['Total Assigned Tasks', total_tasks])
    w.writerow(['Completed Tasks', completed_tasks])
    w.writerow(['Overdue Tasks', overdue_tasks])
    rate = round((completed_tasks / total_tasks * 100) if total_tasks else 0, 1)
    w.writerow(['Completion Rate (%)', rate])
    w.writerow([])
    
    # Submissions Overview
    w.writerow(['--- SUBMISSION & QUALITY ---'])
    subs = Submission.objects.filter(worker=target_user, task__work_module__is_archived=False)
    total_subs = subs.count()
    w.writerow(['Total Submissions', total_subs])
    w.writerow(['Approved Submissions', subs.filter(status='approved').count()])
    w.writerow(['Rejected Submissions', subs.filter(status='rejected').count()])
    scored = subs.filter(score__isnull=False)
    avg_score = round(sum(s.score for s in scored) / scored.count(), 1) if scored.exists() else 0
    w.writerow(['Average Quality Score', avg_score])
    on_time = subs.filter(submitted_at__isnull=False, submitted_at__lte=_F('task__deadline')).count()
    comp = round((on_time / total_subs * 100) if total_subs else 0, 1)
    w.writerow(['On-Time Compliance (%)', comp])
    w.writerow([])
    
    # Attendance Overview
    w.writerow(['--- ATTENDANCE & HOURS (ALL TIME) ---'])
    all_att = AttendanceRecord.objects.filter(user=target_user)
    days_present = all_att.filter(status__in=['present', 'late']).count()
    days_absent = all_att.filter(status='absent').count()
    from django.db.models import Sum
    tot_hours = all_att.aggregate(Sum('total_hours'))['total_hours__sum'] or 0
    w.writerow(['Total Days Present', days_present])
    w.writerow(['Total Days Absent', days_absent])
    w.writerow(['Total Recorded Hours', round(tot_hours, 1)])
    
    return response


@login_required(login_url='login')
def worker_performance(request):
    """My score: this month's KPI score from the KPI engine, how it is made up, six months of history,
    the work behind it and recent reviews. Managers may open the people they work with (?user_id=);
    super admins anyone."""
    from attendance.models import AttendanceRecord
    from django.db.models import Sum, Avg
    from kpi.engine import KPICalculationEngine
    from kpi.models import KPIWeight

    viewer = request.user
    target_user = viewer
    people = None
    if viewer.role in ('manager', 'super_admin'):
        people = (User.objects.filter(is_active=True) if viewer.role == 'super_admin' or viewer.is_superuser
                  else viewer.get_teammates()).exclude(role='super_admin').order_by('first_name', 'last_name', 'email')
        wanted = request.GET.get('user_id')
        if wanted and str(wanted).isdigit():
            target_user = get_object_or_404(people, id=int(wanted)) if int(wanted) != viewer.id else viewer
    is_self = target_user.id == viewer.id

    # ── this month and the five before it (calendar months) ──
    today = timezone.localdate()
    months = []
    y, m = today.year, today.month
    for _ in range(6):
        months.append(_dt.date(y, m, 1))
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    months.reverse()

    w = KPIWeight.get_weights()
    parts_def = [
        ('completion', 'Tasks completed', 'إنجاز المهام', w.completion_rate_weight, 'calculate_completion_rate'),
        ('on_time', 'On time', 'الالتزام بالمواعيد', w.on_time_rate_weight, 'calculate_on_time_rate'),
        ('quality', 'Quality (review score)', 'الجودة (درجة المراجعة)', w.quality_score_weight, 'calculate_quality_score'),
        ('productivity', 'Output (approved work)', 'حجم العمل المعتمد', w.productivity_score_weight, 'calculate_productivity_score'),
    ]
    history = []
    current_parts = []
    from django.core.cache import cache
    for i, month in enumerate(months):
        cache_key = f'wt-kpi-{target_user.id}-{month:%Y%m}-{int(w.updated_at.timestamp())}'
        values = cache.get(cache_key) if i < len(months) - 1 else None  # past months may be a few minutes old
        if values is None:
            # Build the engine without its per-instance weights lookup (the weights are already loaded).
            engine = KPICalculationEngine.__new__(KPICalculationEngine)
            engine.user, engine.month, engine.weights = target_user, month, w
            values = {key: max(0.0, min(100.0, float(getattr(engine, fn)() or 0))) for key, _, _, _, fn in parts_def}
            if i < len(months) - 1:
                cache.set(cache_key, values, 300)
        total = round(min(100.0, sum(values[key] * weight for key, _, _, weight, _ in parts_def)), 1)
        history.append({'month': month, 'label_en': month.strftime('%b'), 'label_ar': _AR_MONTHS[month.month - 1],
                        'score': total, 'is_current': i == len(months) - 1})
        if i == len(months) - 1:
            for key, en, ar, weight, _ in parts_def:
                current_parts.append({'key': key, 'en': en, 'ar': ar, 'value': round(values[key], 1),
                                      'weight': round(weight * 100), 'points': round(values[key] * weight, 1)})
    score = history[-1]['score']
    previous = history[-2]['score'] if len(history) > 1 else None
    change = round(score - previous, 1) if previous is not None else None
    best = max(history, key=lambda h: h['score'])

    # ── the work behind the score ──
    assigned = Task.objects.filter(assigned_to=target_user, work_module__is_archived=False)
    subs = Submission.objects.filter(worker=target_user, task__work_module__is_archived=False)
    now = timezone.now()
    open_tasks = assigned.exclude(status__in=['approved', 'completed'])
    reviewed = subs.filter(score__isnull=False)
    att = AttendanceRecord.objects.filter(user=target_user, date__gte=today - _dt.timedelta(days=30))
    facts = {
        'open': open_tasks.count(),
        'overdue': open_tasks.filter(deadline__lt=now).count(),
        'waiting': subs.filter(status__in=['submitted', 'under_review']).count(),
        'approved': subs.filter(status='approved').count(),
        'sent_back': subs.filter(status='rejected').count(),
        'avg_review': round(reviewed.aggregate(a=Avg('score'))['a'] or 0, 1) if reviewed.exists() else None,
        'days_present': att.filter(status__in=['present', 'late']).count(),
        'hours': round(att.aggregate(h=Sum('total_hours'))['h'] or 0, 1),
    }
    # Reviewed = has a review date, a score, or a final status (older rows lack reviewed_at).
    from django.db.models.functions import Coalesce
    recent_reviews = (subs.filter(Q(reviewed_at__isnull=False) | Q(score__isnull=False) | Q(status__in=['approved', 'rejected']))
                      .select_related('task', 'task__work_module')
                      .annotate(wt_reviewed=Coalesce('reviewed_at', 'updated_at')).order_by('-wt_reviewed')[:8])

    import re as _re
    for r in recent_reviews:
        c = getattr(r.task.work_module, 'color', '') or ''
        r.wt_color = c if _re.fullmatch(r'#[0-9a-fA-F]{3,8}', c) else ''

    context = {
        'target_user': target_user,
        'is_self': is_self,
        'people': people,
        'score': score,
        'score_change': change,
        'best_month': best,
        'parts': current_parts,
        'history': history,
        'facts': facts,
        'recent_reviews': recent_reviews,
        'month_en': today.strftime('%B %Y'),
        'month_ar': f'{_AR_MONTHS[today.month - 1]} {today.year}',
    }
    return render(request, 'pages/worker_performance.html', context)


# ── Improvement #6: Manager Analytics Panel ───────────

@login_required(login_url='login')
def manager_analytics(request):
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    now = timezone.now()
    workers = User.objects.filter(role='worker', is_active=True)
    worker_stats = []
    for w in workers:
        s = Submission.objects.filter(worker=w, task__work_module__is_archived=False)
        total = s.count(); approved = s.filter(status='approved').count()
        scored = s.filter(score__isnull=False)
        avg = round(sum(x.score for x in scored)/scored.count(),1) if scored.exists() else None
        worker_stats.append({
            'user': w, 'total_subs': total, 'approved': approved,
            'approval_rate': round((approved/total*100) if total else 0,1),
            'avg_score': avg,
            'overdue_tasks': Task.objects.filter(assigned_to=w, status='overdue').count(),
        })
    module_health = []
    for m in WorkModule.get_visible_modules(request.user, include_archived=False):
        tasks = Task.objects.filter(work_module=m)
        total = tasks.count(); done = tasks.filter(status__in=['approved','completed']).count()
        module_health.append({
            'module': m, 'total': total, 'done': done,
            'overdue': tasks.filter(status='overdue').count(),
            'health': round((done/total*100) if total else 0, 1),
        })
    monthly_trend = []
    for i in range(5,-1,-1):
        ms = (now.replace(day=1)-_dt.timedelta(days=30*i)).replace(day=1)
        me = (ms.replace(day=28)+_dt.timedelta(days=4)).replace(day=1)
        monthly_trend.append({
            'label': ms.strftime('%b %Y'),
            'submitted': Submission.objects.filter(created_at__gte=ms, created_at__lt=me, task__work_module__is_archived=False).count(),
            'approved': Submission.objects.filter(status='approved', created_at__gte=ms, created_at__lt=me, task__work_module__is_archived=False).count(),
        })
    all_tasks = Task.objects.filter(work_module__is_archived=False)
    all_subs = Submission.objects.filter(score__isnull=False, task__work_module__is_archived=False)
    context = {
        'worker_stats': worker_stats, 'module_health': module_health,
        'total_overdue': all_tasks.filter(status='overdue').count(),
        'total_pending': all_tasks.filter(status='pending').count(),
        'total_completed': all_tasks.filter(status__in=['approved','completed']).count(),
        'global_avg_score': round(sum(s.score for s in all_subs)/all_subs.count(),1) if all_subs.exists() else None,
        'monthly_trend': script_json(monthly_trend),
    }
    return render(request, 'pages/manager_analytics.html', context)


# ── Improvement #9: Avatar Upload ─────────────────────

@login_required(login_url='login')
@require_http_methods(["POST"])
def profile_avatar_upload(request):
    """Replace or remove the profile photo (JPEG, PNG, GIF or WebP, up to 5 MB)."""
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.POST.get('remove') == '1':
        if profile_obj.avatar:
            try: profile_obj.avatar.delete(save=False)
            except Exception: pass
            profile_obj.avatar = None
            profile_obj.save()
        messages.success(request, _say(request, 'Photo removed.', 'تمت إزالة الصورة.'))
        return redirect('profile')
    avatar_file = request.FILES.get('avatar')
    if not avatar_file:
        messages.error(request, _say(request, 'Choose an image first.', 'اختر صورة أولًا.'))
        return redirect('profile')
    if avatar_file.size > 5 * 1024 * 1024:
        messages.error(request, _say(request, 'The photo must be under 5 MB.', 'يجب أن يكون حجم الصورة أقل من 5 ميغابايت.'))
        return redirect('profile')
    from core.uploads import BadImage, process_photo
    try:
        clean = process_photo(avatar_file)
    except BadImage:
        messages.error(request, _say(request, 'Use a JPEG, PNG, GIF or WebP image.', 'استخدم صورة بصيغة JPEG أو PNG أو GIF أو WebP.'))
        return redirect('profile')
    if profile_obj.avatar:
        try: profile_obj.avatar.delete(save=False)
        except Exception: pass
    profile_obj.avatar.save(clean.name, clean, save=False)
    profile_obj.save()
    messages.success(request, _say(request, 'Photo updated.', 'تم تحديث الصورة.'))
    return redirect('profile')


# ── Improvement #12: Kanban Board ─────────────────────

@login_required(login_url='login')
def task_kanban(request):
    if request.user.role == 'super_admin':
        qs = Task.objects.filter(work_module__is_archived=False).select_related('work_module','created_by').prefetch_related('assigned_to')
        modules = WorkModule.objects.filter(is_archived=False).select_related('group_link').order_by('order', 'name')
    elif request.user.role == 'manager':
        visible_modules = WorkModule.get_visible_modules(request.user)
        qs = Task.objects.filter(work_module__is_archived=False).filter(
            Q(work_module__in=visible_modules) | Q(created_by=request.user) | Q(assigned_to=request.user)
        ).select_related('work_module','created_by').prefetch_related('assigned_to').distinct()
        modules = visible_modules.filter(is_archived=False).select_related('group_link').order_by('order', 'name')
    else:
        qs = Task.objects.filter(assigned_to=request.user, work_module__is_archived=False).select_related('work_module','created_by').prefetch_related('assigned_to')
        modules = WorkModule.objects.filter(id__in=qs.values_list('work_module_id', flat=True)).distinct().order_by('name')

    qs = qs.annotate(wt_comments=Count('comments', distinct=True), wt_subs=Count('submissions', distinct=True))
    columns = {
        'pending':     {'en': 'Not started', 'ar': 'لم تبدأ',         'tasks': []},
        'in_progress': {'en': 'In progress', 'ar': 'قيد التنفيذ',     'tasks': []},
        'submitted':   {'en': 'Submitted',   'ar': 'تم التسليم',      'tasks': []},
        'rejected':    {'en': 'Sent back',   'ar': 'أُعيدت للتعديل',  'tasks': []},
        'approved':    {'en': 'Done',        'ar': 'مكتملة',          'tasks': []},
        'overdue':     {'en': 'Overdue',     'ar': 'متأخرة',          'tasks': []},
    }
    for task in qs:
        col = 'approved' if task.status == 'completed' else (task.status if task.status in columns else 'pending')
        columns[col]['tasks'].append(task)
    return render(request, 'pages/task_kanban.html', {'columns': columns, 'modules': modules})



@login_required(login_url='login')
@require_http_methods(["POST"])
def task_kanban_move(request, task_id):
    if request.user.role not in ['manager','super_admin']:
        return JsonResponse({'error':'Permission denied'}, status=403)
    task = get_object_or_404(Task, id=task_id)
    new_status = request.POST.get('status')
    if new_status not in ['pending','in_progress','submitted','approved','rejected','overdue']:
        return JsonResponse({'error':'Invalid status'}, status=400)
    task.status = new_status
    task.save(update_fields=['status','updated_at'])
    return JsonResponse({'success': True, 'task_id': task.id, 'new_status': new_status, 'new_status_display': task.get_status_display()})


# ── Improvement #13: Calendar View ────────────────────

@login_required(login_url='login')
def task_calendar(request):
    if request.user.role == 'super_admin':
        qs = Task.objects.filter(work_module__is_archived=False).select_related('work_module')
    elif request.user.role == 'manager':
        visible_modules = WorkModule.get_visible_modules(request.user)
        qs = Task.objects.filter(work_module__is_archived=False).filter(
            Q(work_module__in=visible_modules) | Q(created_by=request.user) | Q(assigned_to=request.user)
        ).select_related('work_module').distinct()
    else:
        qs = Task.objects.filter(assigned_to=request.user, work_module__is_archived=False).select_related('work_module')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        status_filter = request.GET.get('status', '').strip()
        search_query = request.GET.get('query', '').strip()
        if status_filter and status_filter != 'all':
            qs = qs.filter(status=status_filter)
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query) |
                Q(work_module__name__icontains=search_query)
            )

        events = [
            {
                'id': t.id,
                'title': t.title,
                'start': t.deadline.isoformat() if t.deadline else None,
                'url': t.detail_url,
                'classNames': ['wt-ev', 'is-' + ('approved' if t.status == 'completed' else t.status)],
                'extendedProps': {
                    'status': t.status,
                    'priority': t.priority,
                    'module': t.work_module.name if t.work_module else ''
                }
            }
            for t in qs
        ]
        return JsonResponse(events, safe=False)

    today = timezone.localdate()
    week_end = today + timezone.timedelta(days=(6 - today.weekday()))
    stats = {
        'total': qs.count(),
        'pending': qs.filter(status='pending').count(),
        'in_progress': qs.filter(status='in_progress').count(),
        'completed': qs.filter(status__in=['approved', 'completed']).count(),
        'overdue': qs.filter(status='overdue').count(),
        'today': qs.filter(deadline__date=today).count(),
        'this_week': qs.filter(deadline__date__gte=today, deadline__date__lte=week_end).count(),
        'this_month': qs.filter(deadline__date__year=today.year, deadline__date__month=today.month).count(),
    }
    stats['completed_pct'] = round(stats['completed'] * 100 / max(stats['total'], 1))
    stats['pending_pct'] = round(stats['pending'] * 100 / max(stats['total'], 1))
    stats['overdue_pct'] = round(stats['overdue'] * 100 / max(stats['total'], 1))
    stats['today_pct'] = round(stats['today'] * 100 / max(stats['total'], 1))
    stats['week_pct'] = round(stats['this_week'] * 100 / max(stats['total'], 1))
    stats['month_pct'] = round(stats['this_month'] * 100 / max(stats['total'], 1))

    return render(request, 'pages/task_calendar.html', {'stats': stats})


# ── Improvement #14: Dark Mode Setter ─────────────────

@login_required(login_url='login')
@require_http_methods(["POST"])
def set_dark_mode(request):
    mode = request.POST.get('mode','light')
    request.session['dark_mode'] = (mode == 'dark')
    return JsonResponse({'success': True, 'dark_mode': mode == 'dark'})


# ── Improvement #15: Bulk Task Actions ────────────────

@login_required(login_url='login')
@require_http_methods(["POST"])
def task_bulk_action(request):
    if request.user.role not in ['manager','super_admin']:
        return JsonResponse({'error':'Permission denied'}, status=403)
    action = request.POST.get('action','')
    task_ids = [int(x) for x in request.POST.get('task_ids','').split(',') if x.strip().isdigit()]
    if not task_ids:
        return JsonResponse({'error':'No tasks selected'}, status=400)
    qs = Task.objects.filter(id__in=task_ids)
    if action == 'delete':
        cnt = qs.count(); qs.delete()
        return JsonResponse({'success':True,'message':f'{cnt} tasks deleted.'})
    elif action.startswith('status_'):
        ns = action[7:]
        if ns not in ['pending','in_progress','approved','rejected','overdue']:
            return JsonResponse({'error':'Invalid status'}, status=400)
        cnt = qs.update(status=ns, updated_at=timezone.now())
        return JsonResponse({'success':True,'message':f'{cnt} tasks set to {ns}.'})
    elif action.startswith('priority_'):
        np = action[9:]
        if np not in ['low','medium','high','critical']:
            return JsonResponse({'error':'Invalid priority'}, status=400)
        cnt = qs.update(priority=np, updated_at=timezone.now())
        return JsonResponse({'success':True,'message':f'{cnt} tasks set to {np} priority.'})
    elif action == 'assign':
        uid = request.POST.get('assign_to_user_id')
        tu = get_object_or_404(User, id=uid)
        for t in qs: t.assigned_to.add(tu)
        return JsonResponse({'success':True,'message':f'Assigned {qs.count()} tasks to {tu.get_full_name()}.'})
    return JsonResponse({'error':'Unknown action'}, status=400)


# ── Improvement #10: Submission Version Comparison ────

@login_required(login_url='login')
def submission_versions(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    worker = request.user
    if request.user.role in ['manager','super_admin']:
        wid = request.GET.get('worker_id', request.user.id)
        worker = get_object_or_404(User, id=wid)
    submission = Submission.objects.filter(task=task, worker=worker).first()
    snapshots = []
    if submission:
        snapshots = submission.versions.all().order_by('version_number')
    
    return render(request, 'pages/submission_versions.html',
                  {'task': task, 'submission': submission, 'snapshots': snapshots, 'target_worker': worker})


@login_required(login_url='login')
def version_data_archive(request):
    """
    Comprehensive System Version Archive & Database Management.
    Supports atomic online SQLite backup creation, safe database restoration
    with auto-safety rollback, file download, backup deletion, and file import.
    Also retains historical SubmissionVersion snapshot logs.
    """
    from core.backup_service import (
        list_backups, create_backup, restore_backup, delete_backup, 
        save_uploaded_backup, get_database_stats, BACKUPS_DIR
    )
    from django.http import FileResponse, Http404

    # 1. Handle File Download
    if request.method == 'GET' and request.GET.get('action') == 'download':
        if getattr(request.user, 'role', '') not in ['super_admin', 'manager']:
            messages.error(request, 'Permission denied.')
            return redirect('version-data-archive')
        b_id = request.GET.get('id', '').strip()
        backups = list_backups()
        target = next((b for b in backups if b.get('id') == b_id), None)
        if not target or not target.get('filename'):
            messages.error(request, 'Requested backup file not found.')
            return redirect('version-data-archive')
        file_path = BACKUPS_DIR / target['filename']
        if not file_path.exists():
            messages.error(request, 'Backup file missing from storage.')
            return redirect('version-data-archive')
        try:
            response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=target['filename'])
            response['Content-Type'] = 'application/x-sqlite3'
            return response
        except Exception as e:
            messages.error(request, f'Download failed: {e}')
            return redirect('version-data-archive')

    # 2. Handle POST Actions (Create, Restore, Delete, Upload)
    if request.method == 'POST':
        if getattr(request.user, 'role', '') != 'super_admin':
            messages.error(request, 'Permission denied. Super Administrator access required for database operations.')
            return redirect('version-data-archive')

        action = request.POST.get('action', '').strip()

        if action == 'create':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            try:
                b = create_backup(name=name, description=description, user=request.user)
                messages.success(request, f"New system backup '{b.get('name')}' created successfully ({b.get('size_human')}).")
            except Exception as e:
                messages.error(request, f"Failed to create backup: {e}")
            return redirect('version-data-archive')

        elif action == 'restore':
            backup_id = request.POST.get('backup_id', '').strip()
            try:
                b = restore_backup(backup_id=backup_id, user=request.user)
                messages.success(request, f"System database successfully restored to '{b.get('name')}'. Live state reloaded.")
            except Exception as e:
                messages.error(request, f"Failed to restore database: {e}")
            return redirect('version-data-archive')

        elif action == 'delete':
            backup_id = request.POST.get('backup_id', '').strip()
            try:
                ok = delete_backup(backup_id=backup_id)
                if ok:
                    messages.success(request, "Backup version deleted successfully from storage.")
                else:
                    messages.warning(request, "Backup not found or already removed.")
            except Exception as e:
                messages.error(request, f"Failed to delete backup: {e}")
            return redirect('version-data-archive')

        elif action == 'upload':
            if 'backup_file' not in request.FILES:
                messages.error(request, "Please select a valid .sqlite3 or .db backup file to upload.")
                return redirect('version-data-archive')
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            try:
                b = save_uploaded_backup(request.FILES['backup_file'], name=name, description=description, user=request.user)
                messages.success(request, f"Backup '{b.get('name')}' imported successfully and ready for restoration.")
            except Exception as e:
                messages.error(request, f"Import failed: {e}")
            return redirect('version-data-archive')

    # 3. Handle GET View Rendering
    backups = list_backups()
    db_stats = get_database_stats()

    # SubmissionVersion Snapshots Query (for Tab 2)
    snapshots = SubmissionVersion.objects.select_related('submission__task', 'submission__worker').all()
    task_id = request.GET.get('task_id')
    task = None
    if task_id:
        snapshots = snapshots.filter(submission__task_id=task_id)
        from tasks.models import Task
        task = Task.objects.filter(id=task_id).first()

    if request.user.role == 'worker':
        snapshots = snapshots.filter(submission__worker=request.user)

    search = request.GET.get('search', '')
    if search:
        snapshots = snapshots.filter(
            Q(submission__task__title__icontains=search) |
            Q(submission__worker__first_name__icontains=search) |
            Q(submission__worker__last_name__icontains=search) |
            Q(notes__icontains=search)
        )

    worker_id = request.GET.get('worker')
    if worker_id:
        snapshots = snapshots.filter(submission__worker_id=worker_id)

    status = request.GET.get('status')
    if status:
        snapshots = snapshots.filter(status=status)

    last_backup = backups[0] if backups else None
    active_tab = request.GET.get('tab', 'backups')

    context = {
        'backups': backups,
        'db_stats': db_stats,
        'last_backup': last_backup,
        'snapshots': snapshots[:150],
        'search': search,
        'task': task,
        'active_tab': active_tab,
    }

    return render(request, 'pages/version_data_archive.html', context)



# =====================================================================
# Submission Summary Exports
# =====================================================================

def _build_summary_data(task):
    """Shared helper: build a matrix of submissions + field values for export."""
    all_subs = (
        Submission.objects
        .filter(task=task)
        .prefetch_related('field_values__field', 'worker')
        .order_by('worker__first_name', 'worker__last_name')
    )
    fields = list(task.custom_fields.all().order_by('order', 'created_at'))
    matrix = []
    for field in fields:
        row = {
            'field': field,
            'is_numeric': field.field_type == 'number',
            'user_values': [],
            'numeric_values': [],
        }
        for sub in all_subs:
            fv = sub.field_values.filter(field=field).first()
            val = fv.value if fv else ''
            row['user_values'].append({'user': sub.worker, 'value': val, 'sub': sub})
            if field.field_type == 'number' and val:
                try:
                    row['numeric_values'].append(float(val))
                except ValueError:
                    pass
        matrix.append(row)
    return all_subs, matrix


@login_required(login_url='login')
def submission_summary_export_xlsx(request, task_id):
    """Export submission summary as a styled XLSX file."""
    import io
    from openpyxl import Workbook
    from openpyxl.styles import (
        Font, PatternFill, Alignment, Border, Side, GradientFill
    )
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse

    task = get_object_or_404(Task, id=task_id)
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('task-detail', task_id=task_id)

    all_subs, matrix = _build_summary_data(task)
    submitters = list(all_subs)

    # --- Read per-field aggregation method from GET params ---
    # e.g. ?agg_1=avg&agg_2=sum
    def get_field_agg(field_id):
        return request.GET.get(f'agg_{field_id}', 'sum')

    wb = Workbook()
    ws = wb.active
    ws.title = 'Submission Summary'

    # ── Styles ──────────────────────────────────────────────────────────
    dark_bg  = PatternFill('solid', fgColor='0F172A')
    indigo   = PatternFill('solid', fgColor='4F46E5')
    light_bg = PatternFill('solid', fgColor='F8FAFF')
    num_bg   = PatternFill('solid', fgColor='EDE9FE')
    alt_bg   = PatternFill('solid', fgColor='F1F5F9')
    white    = PatternFill('solid', fgColor='FFFFFF')

    hdr_font  = Font(name='Calibri', bold=True, color='FFFFFF', size=11)
    body_font = Font(name='Calibri', size=10)
    bold_font = Font(name='Calibri', bold=True, size=10)
    num_font  = Font(name='Calibri', bold=True, color='5B21B6', size=10)
    res_font  = Font(name='Calibri', bold=True, color='4F46E5', size=11)
    title_font= Font(name='Calibri', bold=True, size=14, color='0F172A')
    sub_font  = Font(name='Calibri', size=10, color='64748B')

    center    = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left      = Alignment(horizontal='left',   vertical='center', wrap_text=True)

    thin = Side(style='thin', color='E2E8F0')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # ── Title block ─────────────────────────────────────────────────────
    ws.merge_cells('A1:' + get_column_letter(len(submitters) + 3) + '1')
    title_cell = ws['A1']
    title_cell.value = f'Submission Summary — {task.title}'
    title_cell.font  = title_font
    title_cell.fill  = dark_bg
    title_cell.alignment = center
    ws.row_dimensions[1].height = 30

    ws.merge_cells('A2:' + get_column_letter(len(submitters) + 3) + '2')
    sub_cell = ws['A2']
    sub_cell.value = (
        f'Task: {task.title}  |  Type: {task.get_task_type_display()}  |  '
        f'Exported: {timezone.now().strftime("%d %b %Y %H:%M")}'
    )
    sub_cell.font  = Font(name='Calibri', size=9, color='94A3B8', italic=True)
    sub_cell.fill  = dark_bg
    sub_cell.alignment = center
    ws.row_dimensions[2].height = 18

    # ── Column headers ───────────────────────────────────────────────────
    header_row = 4
    header_labels = ['Field', 'Type', 'Agg. Method']
    for sub in submitters:
        header_labels.append(sub.worker.get_full_name() or sub.worker.email)
    header_labels.append('Result')

    for col_idx, label in enumerate(header_labels, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=label)
        cell.font      = hdr_font
        cell.fill      = indigo
        cell.alignment = center
        cell.border    = border
    ws.row_dimensions[header_row].height = 22

    # ── Data rows ────────────────────────────────────────────────────────
    AGG_MAP = {'sum': 'Sum', 'avg': 'Average', 'pct': 'Percentage', 'max': 'Maximum', 'min': 'Minimum'}

    for r_idx, row in enumerate(matrix, start=header_row + 1):
        fill = num_bg if row['is_numeric'] else (alt_bg if r_idx % 2 == 0 else white)
        field = row['field']
        agg_method = get_field_agg(field.id)

        # Field name
        c1 = ws.cell(row=r_idx, column=1, value=field.label + (' *' if field.required else ''))
        c1.font = bold_font; c1.fill = fill; c1.alignment = left; c1.border = border

        # Field type
        c2 = ws.cell(row=r_idx, column=2, value=field.get_field_type_display() if hasattr(field, 'get_field_type_display') else field.field_type)
        c2.font = body_font; c2.fill = fill; c2.alignment = center; c2.border = border

        # Agg method
        c3 = ws.cell(row=r_idx, column=3, value=AGG_MAP.get(agg_method, agg_method) if row['is_numeric'] else 'N/A')
        c3.font = body_font; c3.fill = fill; c3.alignment = center; c3.border = border

        # Per-user values
        for u_idx, uv in enumerate(row['user_values'], start=4):
            val = uv['value'] if uv['value'] else '—'
            cx = ws.cell(row=r_idx, column=u_idx, value=val)
            cx.font = num_font if row['is_numeric'] and uv['value'] else body_font
            cx.fill = fill; cx.alignment = center; cx.border = border

        # Aggregated result
        result_col = len(submitters) + 4
        nums = row['numeric_values']
        if row['is_numeric'] and nums:
            if agg_method == 'sum':
                result = sum(nums)
            elif agg_method == 'avg':
                result = sum(nums) / len(nums)
            elif agg_method == 'max':
                result = max(nums)
            elif agg_method == 'min':
                result = min(nums)
            elif agg_method == 'pct':
                total = sum(nums)
                result = ' / '.join(f'{(n/total*100):.1f}%' for n in nums) if total else '0%'
            else:
                result = sum(nums)
            if isinstance(result, float):
                result = round(result, 2)
        else:
            result = 'N/A'
        cr = ws.cell(row=r_idx, column=result_col, value=result)
        cr.font = res_font; cr.fill = light_bg; cr.alignment = center; cr.border = border
        ws.row_dimensions[r_idx].height = 18

    # ── Column widths ─────────────────────────────────────────────────────
    ws.column_dimensions['A'].width = 28
    ws.column_dimensions['B'].width = 14
    ws.column_dimensions['C'].width = 14
    for col in range(4, len(submitters) + 4):
        ws.column_dimensions[get_column_letter(col)].width = 20
    ws.column_dimensions[get_column_letter(len(submitters) + 4)].width = 18

    # ── Freeze panes ─────────────────────────────────────────────────────
    ws.freeze_panes = f'D{header_row + 1}'

    # ── Write & respond ───────────────────────────────────────────────────
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f'submission_summary_{task.id}_{timezone.now().strftime("%Y%m%d")}.xlsx'
    response = HttpResponse(
        buf,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required(login_url='login')
def submission_summary_export_pdf(request, task_id):
    """Export submission summary as a styled PDF using ReportLab."""
    import io
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from django.http import HttpResponse

    task = get_object_or_404(Task, id=task_id)
    if request.user.role not in ['manager', 'super_admin']:
        messages.error(request, 'Permission denied.')
        return redirect('task-detail', task_id=task_id)

    all_subs, matrix = _build_summary_data(task)
    submitters = list(all_subs)

    def get_field_agg(field_id):
        return request.GET.get(f'agg_{field_id}', 'sum')

    AGG_MAP = {'sum': 'Sum', 'avg': 'Average', 'pct': 'Percentage', 'max': 'Maximum', 'min': 'Minimum'}

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    style_title  = ParagraphStyle('title',  parent=styles['Title'],  fontSize=18, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
    style_sub    = ParagraphStyle('sub',    parent=styles['Normal'], fontSize=9,  textColor=colors.HexColor('#64748B'), spaceAfter=12)
    style_label  = ParagraphStyle('label',  parent=styles['Normal'], fontSize=8,  textColor=colors.HexColor('#1E293B'), fontName='Helvetica-Bold')
    style_val    = ParagraphStyle('val',    parent=styles['Normal'], fontSize=8,  textColor=colors.HexColor('#334155'))
    style_num    = ParagraphStyle('num',    parent=styles['Normal'], fontSize=8,  textColor=colors.HexColor('#5B21B6'), fontName='Helvetica-Bold')
    style_result = ParagraphStyle('result', parent=styles['Normal'], fontSize=9,  textColor=colors.HexColor('#4F46E5'), fontName='Helvetica-Bold', alignment=TA_CENTER)

    DARK    = colors.HexColor('#0F172A')
    INDIGO  = colors.HexColor('#4F46E5')
    PURPLE  = colors.HexColor('#EDE9FE')
    LIGHT   = colors.HexColor('#F8FAFF')
    ALT     = colors.HexColor('#F1F5F9')
    WHITE   = colors.white

    story = []

    # Title & metadata
    story.append(Paragraph(f'Submission Summary', style_title))
    story.append(Paragraph(
        f'<b>{task.title}</b> &nbsp;·&nbsp; Type: {task.get_task_type_display()} &nbsp;·&nbsp; '
        f'Exported: {timezone.now().strftime("%d %b %Y %H:%M")}',
        style_sub
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=12))

    # ── Table header ──────────────────────────────────────────────────────
    col_headers = ['Field', 'Type', 'Method']
    for sub in submitters:
        name = sub.worker.get_full_name() or sub.worker.email
        col_headers.append(Paragraph(name[:18], ParagraphStyle('hdr', fontSize=7, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER)))
    col_headers.append(Paragraph('Result', ParagraphStyle('hdrr', fontSize=8, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER)))

    table_data = [col_headers]

    # ── Data rows ─────────────────────────────────────────────────────────
    for r_idx, row in enumerate(matrix):
        field = row['field']
        agg_method = get_field_agg(field.id)
        row_bg = PURPLE if row['is_numeric'] else (ALT if r_idx % 2 == 0 else WHITE)

        data_row = [
            Paragraph('<b>' + field.label + ('*' if field.required else '') + '</b>', style_label),
            Paragraph(field.field_type, style_val),
            Paragraph(AGG_MAP.get(agg_method, agg_method) if row['is_numeric'] else '—', style_val),
        ]

        for uv in row['user_values']:
            val = uv['value'] if uv['value'] else '—'
            p_style = style_num if row['is_numeric'] and uv['value'] else style_val
            data_row.append(Paragraph(str(val), p_style))

        nums = row['numeric_values']
        if row['is_numeric'] and nums:
            if agg_method == 'sum':   result = round(sum(nums), 2)
            elif agg_method == 'avg': result = round(sum(nums)/len(nums), 2)
            elif agg_method == 'max': result = round(max(nums), 2)
            elif agg_method == 'min': result = round(min(nums), 2)
            elif agg_method == 'pct':
                total = sum(nums)
                result = ' / '.join(f'{(n/total*100):.1f}%' for n in nums) if total else '0%'
            else: result = round(sum(nums), 2)
        else:
            result = 'N/A'

        data_row.append(Paragraph(str(result), style_result))
        table_data.append(data_row)

    # ── Column widths ─────────────────────────────────────────────────────
    page_w = landscape(A4)[0] - 3*cm
    fixed_cols = [4*cm, 2.2*cm, 2.2*cm]   # Field / Type / Method
    result_col_w = 2.5*cm
    remaining = page_w - sum(fixed_cols) - result_col_w
    user_col_w = remaining / max(len(submitters), 1)
    col_widths = fixed_cols + [user_col_w] * len(submitters) + [result_col_w]

    # ── Build table ───────────────────────────────────────────────────────
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl_style = [
        # Header row
        ('BACKGROUND',    (0, 0), (-1, 0), INDIGO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 8),
        ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, 0), 'MIDDLE'),
        ('ROWBACKGROUND', (0, 0), (-1, 0), INDIGO),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING',    (0, 0), (-1, 0), 6),
        # Body
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        ('VALIGN',        (0, 1), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (2, 1), (-1, -1), 'CENTER'),
        ('ALIGN',         (0, 1), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING',    (0, 1), (-1, -1), 5),
        # Result column highlight
        ('BACKGROUND',    (-1, 1), (-1, -1), LIGHT),
        ('TEXTCOLOR',     (-1, 1), (-1, -1), INDIGO),
        ('FONTNAME',      (-1, 1), (-1, -1), 'Helvetica-Bold'),
        # Borders
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('LINEBELOW',     (0, 0), (-1, 0),  1,   colors.HexColor('#3730A3')),
    ]
    # Alternate row backgrounds
    for r in range(1, len(matrix) + 1):
        bg = PURPLE if (r <= len(matrix) and matrix[r-1]['is_numeric']) else (ALT if r % 2 == 0 else WHITE)
        tbl_style.append(('BACKGROUND', (0, r), (-2, r), bg))

    tbl.setStyle(TableStyle(tbl_style))
    story.append(tbl)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f'<i>Generated by WorkTrack Pro · {request.user.get_full_name() or request.user.email} · '
        f'{timezone.now().strftime("%d %b %Y %H:%M")}</i>',
        ParagraphStyle('footer', fontSize=7, textColor=colors.HexColor('#94A3B8'), alignment=TA_RIGHT)
    ))

    doc.build(story)
    buf.seek(0)
    filename = f'submission_summary_{task.id}_{timezone.now().strftime("%Y%m%d")}.pdf'
    response = HttpResponse(buf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ─────────────────────────────────────────────────────────────────────────────
# CORRESPONDENCE VIEWS  (separate from Task)
# ─────────────────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def correspondence_list(request):
    """Reuse the existing administrative_correspondence view for the new model.
    Shows both legacy Task-based items AND new Correspondence model items."""
    return administrative_correspondence(request)


@login_required(login_url='login')
def correspondence_detail(request, pk):
    """Detail view for a single Correspondence item with live document panel."""
    corr = get_object_or_404(Correspondence, pk=pk)
    user = request.user

    # Access control
    if corr.work_module and corr.work_module.is_archived and request.user.role != 'super_admin':
        messages.error(request, "This correspondence belongs to an archived module and is no longer accessible.")
        return redirect('dashboard')

    # workers only see their assigned items
    if user.role == 'worker' and not corr.assigned_to.filter(pk=user.pk).exists():
        messages.error(request, "You do not have access to this correspondence.")
        return redirect('admin-correspondence')

    # Acknowledgement data
    ack_qs = corr.acknowledgements.select_related('user').order_by('acknowledged_at')
    total_assigned = corr.assigned_to.count()
    ack_count = ack_qs.count()
    ack_pct = int((ack_count / total_assigned * 100)) if total_assigned > 0 else 0
    user_acknowledged = corr.acknowledgements.filter(user=user).exists()
    # Pre-compute acked user PKs for template use (avoids invalid method-call syntax)
    acked_user_ids = set(corr.acknowledgements.values_list('user_id', flat=True))

    context = {
        'corr': corr,
        'ack_list': ack_qs,
        'total_assigned': total_assigned,
        'ack_count': ack_count,
        'ack_pct': ack_pct,
        'user_acknowledged': user_acknowledged,
        'acked_user_ids': acked_user_ids,
        'attachments': corr.attachments.all(),
        'can_acknowledge': (
            not user_acknowledged and
            (user.role == 'worker' or corr.assigned_to.filter(pk=user.pk).exists())
        ),
        'can_manage': user.role in ('manager', 'super_admin'),
    }
    return render(request, 'pages/correspondence_detail.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def correspondence_acknowledge(request, pk):
    """Mark the current user as having acknowledged this correspondence."""
    corr = get_object_or_404(Correspondence, pk=pk)
    user = request.user

    # Only allow if user is assigned
    if not corr.assigned_to.filter(pk=user.pk).exists() and user.role == 'worker':
        messages.error(request, "You are not assigned to this correspondence.")
        return redirect('correspondence-detail', pk=pk)

    note = request.POST.get('note', '')
    obj, created = CorrespondenceAcknowledgement.objects.get_or_create(
        correspondence=corr,
        user=user,
        defaults={'note': note}
    )
    if created:
        messages.success(request, "You have acknowledged this correspondence.")
    else:
        messages.info(request, "You have already acknowledged this correspondence.")
    return redirect('correspondence-detail', pk=pk)


@login_required(login_url='login')
def correspondence_create(request):
    """Create a new Correspondence item."""
    user = request.user
    if user.role not in ('manager', 'super_admin'):
        messages.error(request, "Only managers can create correspondence.")
        return redirect('admin-correspondence')

    if request.method == 'POST':
        title               = request.POST.get('title', '').strip()
        description         = request.POST.get('description', '')
        correspondence_type = request.POST.get('correspondence_type', 'memo')
        reference_number    = request.POST.get('reference_number', '').strip() or None
        priority            = request.POST.get('priority', 'medium')
        deadline_str        = request.POST.get('deadline', '')
        module_id           = request.POST.get('work_module')
        assigned_ids        = request.POST.getlist('assigned_to')
        attachments_list = request.FILES.getlist('attachment')
        cover_image      = request.FILES.get('cover_image')

        if not title:
            messages.error(request, "Title is required.")
        else:
            deadline = None
            if deadline_str:
                try:
                    deadline = datetime.datetime.strptime(deadline_str, '%Y-%m-%d')
                    deadline = timezone.make_aware(deadline)
                except Exception:
                    pass

            work_module = None
            if module_id:
                work_module = WorkModule.objects.filter(pk=module_id).first()

            corr = Correspondence.objects.create(
                title=title,
                description=description,
                correspondence_type=correspondence_type,
                reference_number=reference_number,
                priority=priority,
                deadline=deadline,
                work_module=work_module,
                created_by=user,
                status='active',
            )
            
            if attachments_list:
                corr.attachment = attachments_list[0]
                
            if cover_image:
                corr.cover_image = cover_image
            corr.save()

            if len(attachments_list) > 1:
                for file in attachments_list[1:]:
                    CorrespondenceAttachment.objects.create(correspondence=corr, file=file)

            if assigned_ids:
                assigned_users = User.objects.filter(pk__in=assigned_ids, is_active=True)
                corr.assigned_to.set(assigned_users)
                for worker in assigned_users:
                    notify_correspondence_assigned(corr, worker)

            messages.success(request, f"Correspondence '{corr.title}' created successfully.")
            return redirect('correspondence-detail', pk=corr.pk)

    # GET — render form, optionally pre-filling from a CorrespondenceTemplate
    modules = WorkModule.objects.filter(is_archived=False).order_by('name')
    assignable_users = user.get_teammates().order_by('first_name', 'last_name')


    # Pre-select module if coming from a module context
    initial_module = None
    module_slug = request.GET.get('module')
    if module_slug:
        initial_module = WorkModule.objects.filter(slug=module_slug).first()

    context = {
        'modules': modules,
        'assignable_users': assignable_users,
        'action': 'create',
        'initial_module': initial_module,
    }
    return render(request, 'pages/correspondence_form.html', context)


@login_required(login_url='login')
def correspondence_edit(request, pk):
    """Edit an existing Correspondence item."""
    user = request.user
    if user.role not in ('manager', 'super_admin'):
        messages.error(request, "Only managers can edit correspondence.")
        return redirect('correspondence-detail', pk=pk)

    corr = get_object_or_404(Correspondence, pk=pk)

    if request.method == 'POST':
        corr.title               = request.POST.get('title', corr.title).strip()
        corr.description         = request.POST.get('description', corr.description)
        corr.correspondence_type = request.POST.get('correspondence_type', corr.correspondence_type)
        corr.reference_number    = request.POST.get('reference_number', '').strip() or None
        corr.priority            = request.POST.get('priority', corr.priority)
        corr.status              = request.POST.get('status', corr.status)
        deadline_str             = request.POST.get('deadline', '')
        module_id                = request.POST.get('work_module')
        assigned_ids             = request.POST.getlist('assigned_to')

        if deadline_str:
            try:
                dl = datetime.datetime.strptime(deadline_str, '%Y-%m-%d')
                corr.deadline = timezone.make_aware(dl)
            except Exception:
                pass

        if module_id:
            corr.work_module = WorkModule.objects.filter(pk=module_id).first()
        else:
            corr.work_module = None

        if 'attachment' in request.FILES:
            attachments_list = request.FILES.getlist('attachment')
            if not corr.attachment and attachments_list:
                corr.attachment = attachments_list[0]
                attachments_list = attachments_list[1:]
                
            for file in attachments_list:
                CorrespondenceAttachment.objects.create(correspondence=corr, file=file)
                
        if 'cover_image' in request.FILES:
            corr.cover_image = request.FILES['cover_image']
        elif request.POST.get('clear_cover_image') == '1':
            corr.cover_image = None
            
        if request.POST.get('clear_attachment') == '1':
            corr.attachment = None
            
        delete_att_ids = request.POST.getlist('delete_attachment')
        if delete_att_ids:
            CorrespondenceAttachment.objects.filter(id__in=delete_att_ids, correspondence=corr).delete()

        corr.save()

        if assigned_ids:
            assigned_users = User.objects.filter(pk__in=assigned_ids, is_active=True)
            # Find newly assigned workers to notify only them (optional, following task_create pattern)
            # Actually task_create pattern notifies all assigned upon creation. 
            # For edit, let's notify only the newly added ones for better UX.
            old_assigned_ids = set(corr.assigned_to.values_list('id', flat=True))
            new_assigned_ids = set(int(aid) for aid in assigned_ids)
            added_ids = new_assigned_ids - old_assigned_ids
            
            corr.assigned_to.set(assigned_users)
            
            if added_ids:
                added_users = User.objects.filter(id__in=added_ids)
                for worker in added_users:
                    notify_correspondence_assigned(corr, worker)

        messages.success(request, "Correspondence updated.")
        return redirect('correspondence-detail', pk=corr.pk)

    # GET
    modules = WorkModule.objects.filter(is_archived=False).order_by('name')
    assignable_users = user.get_teammates().order_by('first_name', 'last_name')
    attachments = CorrespondenceAttachment.objects.filter(correspondence=corr)
    context = {
        'corr': corr,
        'modules': modules,
        'assignable_users': assignable_users,
        'action': 'edit',
        'attachments': attachments,
    }
    return render(request, 'pages/correspondence_form.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def correspondence_delete(request, pk):
    """Delete a Correspondence item."""
    user = request.user
    if user.role not in ('manager', 'super_admin'):
        messages.error(request, "Only managers can delete correspondence.")
        return redirect('correspondence-detail', pk=pk)
    corr = get_object_or_404(Correspondence, pk=pk)
    corr.delete()
    messages.success(request, "Correspondence deleted.")
    return redirect('admin-correspondence')


@login_required(login_url='login')
def offline_map_manager(request):
    """View for managing offline map tiles across the entire application."""
    # Get all tasks with location enabled to support batch sync
    tasks_with_loc = Task.objects.filter(location_enabled=True).select_related('work_module')
    
    # Extract coordinates for the frontend
    task_locations = []
    for t in tasks_with_loc:
        if t.latitude and t.longitude:
            task_locations.append({
                'id': t.id,
                'title': t.title,
                'lat': float(t.latitude),
                'lng': float(t.longitude),
                'module': t.work_module.name if t.work_module else 'No Module'
            })
            
    context = {
        'task_locations': script_json(task_locations),
        'task_count': tasks_with_loc.count(),
    }
    return render(request, 'pages/offline_map_manager.html', context)


def map_tile_proxy(request, layer_type, z, x, y):
    """
    Proxies map tiles from external sources and saves them permanently 
    to the server's filesystem for true offline deployment.
    """
    # Define source URL patterns
    if layer_type == 'satellite':
        # Esri World Imagery uses Z/Y/X
        source_url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    else: # street / carto
        # Carto Voyager uses a subdomain {s} usually a,b,c,d
        subdomain = 'a' 
        source_url = f"https://{subdomain}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png"

    # Define local path in media
    tile_dir = os.path.join(django_settings.MEDIA_ROOT, 'map_tiles', layer_type, str(z), str(x))
    tile_path = os.path.join(tile_dir, f"{y}.png")

    # 1. Check if we already have it locally
    if os.path.exists(tile_path):
        try:
            f = open(tile_path, 'rb')
            header = f.read(4)
            f.seek(0)
            if header.startswith(b'\xff\xd8'):
                content_type = 'image/jpeg'
            elif header.startswith(b'\x89PNG'):
                content_type = 'image/png'
            else:
                content_type = 'image/png' # Fallback
            return FileResponse(f, content_type=content_type)
        except Exception:
            pass # Fallback to download if file is corrupted

    # 2. If not, download and "Permanentize" it
    try:
        os.makedirs(tile_dir, exist_ok=True)
        headers = {'User-Agent': 'WorkTrack-Pro-Offline-Hub/1.0'}
        response = requests.get(source_url, timeout=15, headers=headers)
        
        if response.status_code == 200:
            with open(tile_path, 'wb') as f:
                f.write(response.content)
            return HttpResponse(response.content, content_type=response.headers.get('Content-Type', 'image/png'))
        else:
            # If server is offline and we don't have the tile, we hit this
            return HttpResponse(status=response.status_code)
    except Exception as e:
        print(f"Tile proxy error: {str(e)}")
        return HttpResponse(status=404)

# ==========================================
# IMPERSONATION (LOGIN AS) FEATURE
# ==========================================

@login_required(login_url='login')
def login_as_page(request):
    """Page for super_admins to select a user to impersonate."""
    # Also allow if they are currently impersonating and want to switch again (check session)
    is_impersonating = 'impersonator_id' in request.session
    if request.user.role != 'super_admin' and not is_impersonating:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
        
    search = request.GET.get('search', '')
    
    # Original admin we should exclude
    admin_id = request.session.get('impersonator_id', request.user.id)
    users = User.objects.exclude(id=admin_id).order_by('-date_joined')
    
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search) | Q(first_name__icontains=search))
        
    return render(request, 'pages/login_as.html', {
        'users': users,
        'search': search,
    })

@login_required(login_url='login')
@require_http_methods(["POST"])
def impersonate_user(request, user_id):
    """Enable a super_admin to seamlessly login as another user."""
    is_impersonating = 'impersonator_id' in request.session
    if request.user.role != 'super_admin' and not is_impersonating:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
        
    target_user = get_object_or_404(User, id=user_id)
    # Re-use existing impersonator ID if switching users mid-impersonation
    original_admin_id = request.session.get('impersonator_id', request.user.id)
    
    # Use login to authenticate target user
    login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')
    
    # Store the original super admin identity in the fresh session
    request.session['impersonator_id'] = original_admin_id
    messages.success(request, f'You are now operating as {target_user.username}.')
    return redirect('dashboard')

@login_required(login_url='login')
def revert_impersonation(request):
    """Reverts an impersonated session back to the original super_admin."""
    impersonator_id = request.session.get('impersonator_id')
    if not impersonator_id:
        messages.error(request, 'No active impersonation session found.')
        return redirect('dashboard')
        
    admin_user = get_object_or_404(User, id=impersonator_id)
    
    # Log back into the real admin user
    login(request, admin_user, backend='django.contrib.auth.backends.ModelBackend')
    
    messages.success(request, 'Successfully returned to your Admin account.')
    return redirect('dashboard')

@login_required(login_url='login')
@require_http_methods(["GET"])
def available_modules(request):
    """View to list modules available for open enrollment."""
    user = request.user
    
    # Get modules that allow enrollment
    available_qs = WorkModule.objects.filter(allow_enrollment=True, is_archived=False)
    
    # Exclude modules the user is already assigned to (if they are a worker)
    # A user is technically "assigned" if they have tasks in that module
    enrolled_task_module_ids = Task.objects.filter(assigned_to=user).values_list('work_module_id', flat=True).distinct()
    enrolled_users_ids = user.enrolled_modules.values_list('id', flat=True)
    all_enrolled_ids = set(list(enrolled_task_module_ids) + list(enrolled_users_ids))
    
    available_qs = available_qs.exclude(id__in=all_enrolled_ids)

    # Order by newest
    available_qs = available_qs.order_by('-created_at')

    context = {
        'title': 'Available Modules',
        'modules': available_qs,
    }
    return render(request, 'pages/available_modules.html', context)

@login_required(login_url='login')
@require_http_methods(["POST"])
def enroll_module(request, module_slug):
    """Action to enroll a user in a module and all its tasks."""
    module = get_object_or_404(WorkModule, slug=module_slug)
    
    if not module.allow_enrollment:
        messages.error(request, 'This module is not open for enrollment.')
        return redirect('dashboard')
        
    user = request.user
    
    # Save the explicit enrollment
    module.enrolled_users.add(user)
    
    # Assign the user to all standard tasks in the module
    tasks = module.tasks.all()
    assigned_count = 0
    for task in tasks:
        if not task.assigned_to.filter(id=user.id).exists():
            task.assigned_to.add(user)
            assigned_count += 1
            
    # Also assign to correspondence (using the newer Correspondence model)
    correspondences = module.correspondences.all()
    for corr in correspondences:
        if not corr.assigned_to.filter(id=user.id).exists():
            corr.assigned_to.add(user)
            
    messages.success(request, f'Successfully enrolled in {module.name}! Added to {assigned_count} tasks.')
    return redirect('module-dashboard', module_slug=module.slug)


@login_required
def global_map(request):
    from tasks.models import Task
    import json
    from django.db import models
    
    # Filter based on roles
    if request.user.role == 'super_admin':
        tasks = Task.objects.filter(location_enabled=True)
    elif request.user.role == 'manager':
        # Manager sees tasks in their modules or assigned to them
        visible_modules = WorkModule.get_visible_modules(request.user)
        tasks = Task.objects.filter(
            location_enabled=True
        ).filter(
            models.Q(work_module__in=visible_modules) |
            models.Q(assigned_to=request.user) |
            models.Q(created_by=request.user)
        ).distinct()
    else:
        # Normal worker
        visible_modules = WorkModule.get_visible_modules(request.user)
        tasks = Task.objects.filter(
            location_enabled=True
        ).filter(
            models.Q(assigned_to=request.user) |
            models.Q(created_by=request.user) |
            models.Q(work_module__in=visible_modules, work_module__is_shared=True) |
            models.Q(work_module__enrolled_users=request.user)
        ).distinct()
        
    tasks_data = []
    for t in tasks:
        if t.latitude and t.longitude:
            assignees = [u.get_full_name() for u in t.assigned_to.all()]
            tasks_data.append({
                'id': t.id,
                'title': t.title,
                'description': t.description[:100] + '...' if len(t.description) > 100 else t.description,
                'status': t.status,
                'status_display': t.get_status_display(),
                'lat': t.latitude,
                'lng': t.longitude,
                'deadline': t.deadline.strftime('%Y-%m-%d %H:%M') if t.deadline else '',
                'assigned_users': ', '.join(assignees) if assignees else 'Unassigned',
                'url': f'/tasks/{t.id}/'
            })
    
    context = {
        'tasks_json': script_json(tasks_data),
    }
    return render(request, 'pages/global_map.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def reset_database_ajax(request):
    """
    Super Admin Quick Tool: Reset the database and optionally seed the 
    Faculty of Law and Political Science (University of Ghardaia) structure.
    Protects 1 super admin and the contact-submissions module.
    """
    if request.user.role != 'super_admin' and not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Access denied. Super Admin privileges required.'}, status=403)
    
    try:
        data = {}
        if request.content_type == 'application/json' and request.body:
            import json
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST

        mode = data.get('mode', 'faculty_seeded')  # 'faculty_seeded' or 'empty_only'
        empty_only = (mode == 'empty_only')
        
        from core.faculty_seeder import reset_and_seed_faculty
        result = reset_and_seed_faculty(keep_user_id=request.user.id, empty_only=empty_only)
        
        if result.get("success"):
            return JsonResponse({
                'status': 'success',
                'message': result.get('message', 'Database reset successfully.'),
                'data': result
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': result.get('error', 'Reset operation failed.')
            }, status=500)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Server error: {str(e)}'}, status=500)

