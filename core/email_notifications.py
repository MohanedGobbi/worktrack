"""
core/email_notifications.py

Central email notification sender.
Respects NotificationPreference settings per user.
Used by views and management commands.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from notifications.models import Notification, EmailTemplate, EmailStyle
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.html import escape
import datetime
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def _get_pref(user):
    return getattr(user, 'notification_preference', None)


def _get_abs_url(path):
    if not path:
        return None
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    return f"{site_url}{path}"


def render_premium_email(n_type, title, body_content, recipient, extra_context=None, style_override=None):
    """
    Renders a premium HTML email using dynamic templates and global styling.
    """
    # 1. Get Global Style
    style = EmailStyle.objects.first()
    if not style:
        # Create default if not exists
        style = EmailStyle.objects.create()

    # 2. Get/Create Template for this notification type
    template_obj, created = EmailTemplate.objects.get_or_create(
        notification_type=n_type,
        defaults={
            'subject': f'[WorkTrack Pro] {title}',
            # Never store the first message as the template: it would freeze
            # that text for every later email and treat user text as markup.
            'body': 'Hello {recipient_name},\n\n{message}',
            'is_html': True
        }
    )

    # 3. Context for placeholders
    now = timezone.now()
    
    # Helper to get style value (override or DB)
    def s(key, default=None):
        if style_override and style_override.get(key):
            return style_override[key]
        return getattr(style, key, default)

    context_data = {
        'title': title,
        'recipient_name': recipient.get_full_name() or recipient.email,
        'company_name': s('company_name'),
        'primary_color': s('primary_color'),
        'secondary_color': s('secondary_color'),
        'logo_url': _get_abs_url(s('logo_url')) if s('logo_url') else 'https://images.unsplash.com/photo-1454165833767-02a6e30aa576?q=80&w=1000',
        'footer_text': s('footer_text'),
        'notification_label': template_obj.get_notification_type_display().split()[-1].upper() if template_obj.notification_type else "ALERT",
        'date': now.strftime('%b %d, %Y'),
        'status': 'Active',
        'priority': 'High',
        'progress': '0',
        'overall_completion': '0',
        'evaluation': '0',
        'days': '00',
        'hours': '00',
        'minutes': '00',
        'recipient_name': recipient.get_full_name() or recipient.email,
        'user_name': recipient.get_full_name() or recipient.email,
        'task_title': title,
        'message': body_content,
        'banner_image': _get_abs_url(s('logo_url')) if s('logo_url') else 'https://images.unsplash.com/photo-1454165833767-02a6e30aa576?q=80&w=1000',
    }

    if extra_context:
        # Normalize keys (some templates use different naming)
        if 'progress' in extra_context:
            extra_context['overall_completion'] = extra_context['progress']
            extra_context['evaluation'] = extra_context['progress']
        
        context_data.update(extra_context)
        
        # Calculate countdown if deadline is provided
        deadline = extra_context.get('deadline_obj')
        if deadline:
            # Handle string to datetime if serialized
            if isinstance(deadline, str):
                from django.utils.dateparse import parse_datetime
                parsed = parse_datetime(deadline)
                if parsed:
                    deadline = parsed
            
            # Handle naive datetime
            if isinstance(deadline, datetime.datetime) and timezone.is_naive(deadline):
                deadline = timezone.make_aware(deadline)
                
            if isinstance(deadline, datetime.datetime) and deadline > now:
                diff = deadline - now
                context_data['days'] = f"{diff.days:02}"
                context_data['hours'] = f"{(diff.seconds // 3600):02}"
                context_data['minutes'] = f"{(diff.seconds % 3600 // 60):02}"

    # Handle cover_image_url override for hero banner (ensure absolute)
    if extra_context and extra_context.get('cover_image_url'):
        context_data['logo_url'] = _get_abs_url(extra_context['cover_image_url'])
        context_data['banner_image'] = context_data['logo_url']
    else:
        # Ensure default logo is absolute
        context_data['logo_url'] = context_data['banner_image']

    # 4. Replace placeholders like {placeholder}
    # Values come from users (task titles, names, messages), so they are
    # escaped for the HTML body and never compiled as template code. The
    # admin-written template text itself is trusted and kept as written.
    def replace_placeholders(text, context, html):
        if not text: return ""
        for key, value in context.items():
            if value is not None:
                value = str(value)
                if html:
                    value = str(escape(value)).replace(chr(13), '').replace(chr(10), '<br>')
                else:
                    value = ' '.join(value.split())  # no header line breaks
                text = text.replace(f'{{{key}}}', value)
        return text

    rendered_subject = replace_placeholders(template_obj.subject, context_data, html=False)
    rendered_body = replace_placeholders(template_obj.body, context_data, html=True)
    if '<' not in template_obj.body:
        # Plain-text template: keep its line breaks in the HTML email.
        rendered_body = rendered_body.replace('\r\n', '\n').replace('\n', '<br>\n')

    context_data['body'] = mark_safe(rendered_body)

    # 6. Render base template
    html_content = render_to_string('notifications/base_email.html', context_data)
    
    return rendered_subject, html_content


def notify(recipient, n_type, title, message, obj_type='', obj_id=None,
           email_flag_name='email_on_task_assigned', subject=None, extra_context=None):
    """
    Create an in-app notification and optionally send an email.
    """
    # Create in-app notification
    Notification.objects.create(
        recipient=recipient,
        notification_type=n_type,
        title=title,
        message=message,
        related_object_type=obj_type,
        related_object_id=obj_id,
    )

    # Automatically enhance extra_context if obj_type is Task/Correspondence
    if obj_type and obj_id and not extra_context:
        try:
            from tasks.models import Task
            task_obj = Task.objects.get(id=obj_id)
            extra_context = {
                'status': task_obj.get_status_display(),
                'priority': task_obj.get_priority_display(),
                'progress': str(task_obj.progress),
                'deadline_obj': task_obj.deadline,
                'action_url': _get_abs_url(f"/tasks/{task_obj.id}/"),
                'cover_image_url': task_obj.cover_image.url if task_obj.cover_image else None
            }
        except Exception:
            pass

    # Send email if preferences allow and email is configured
    master_switch = getattr(recipient, 'email_notifications', True)
    if not master_switch:
        return

    should_email = False
    user_flag_map = {
        'email_on_task_assigned': 'task_notifications',
        'email_on_submission_received': 'submission_notifications',
    }
    custom_user_flag = user_flag_map.get(email_flag_name)
    if custom_user_flag and hasattr(recipient, custom_user_flag):
        should_email = getattr(recipient, custom_user_flag)
    else:
        pref = _get_pref(recipient)
        should_email = pref and getattr(pref, email_flag_name, False)

    has_email = bool(recipient.email)
    has_smtp = bool(getattr(settings, 'EMAIL_HOST_USER', ''))

    if should_email and has_email and (has_smtp or settings.DEBUG):
        def _async_send_email():
            try:
                from .tasks import send_email_notification_task

                # Use premium rendering
                dynamic_subject, html_body = render_premium_email(n_type, title, message, recipient, extra_context=extra_context)

                email_subject = subject if subject else dynamic_subject

                # Trigger Celery task or send via task
                send_email_notification_task.delay(recipient.email, email_subject, html_body)
                logger.info(f"Async email task (premium) queued for {recipient.email}")

            except Exception as e:
                logger.error(f"Failed to queue email task for {recipient.email}: {str(e)}")

        import threading
        threading.Thread(target=_async_send_email, daemon=True).start()


def notify_task_assigned(task, worker):
    """Notify a worker that they have been assigned a task or correspondence."""
    deadline_str = "N/A"
    if task.deadline:
        if hasattr(task.deadline, 'strftime'):
            deadline_str = task.deadline.strftime("%Y-%m-%d %H:%M")
        else:
            deadline_str = str(task.deadline)

    is_corr = task.task_type == 'correspondence'
    
    if is_corr:
        corr_label = task.get_correspondence_type_display() or "Correspondence"
        title = f'New {corr_label} Issued: {task.title}'
        subject = f'Administrative Correspondence: {task.title}'
        body = (
            f'You have been issued a new administrative {corr_label.lower()}: "{task.title}".\n\n'
            f'Reference: {task.reference_number or "N/A"}\n'
            f'Deadline: {deadline_str}\n\n'
            f'Action Required: Please log in to WorkTrack Pro to acknowledge receipt of this {corr_label.lower()}.'
        )
    else:
        title = f'New Task Assigned: {task.title}'
        subject = f'New Assignment: {task.title}'
        body = (
            f'You have been assigned a new task: "{task.title}".\n\n'
            f'Priority: {task.get_priority_display()}\n'
            f'Deadline: {deadline_str}\n\n'
            f'Please log in to review the task details and begin work.'
        )

    # Append dashboard link
    dashboard_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    body += f'\n\nView Dashboard: {dashboard_url}'

    # Get absolute cover image URL
    cover_image_url = _get_abs_url(task.cover_image.url) if task.cover_image else None

    extra_context = {
        'status': task.get_status_display(),
        'priority': task.get_priority_display(),
        'progress': str(task.progress),
        'cover_image_url': cover_image_url,
        'deadline_obj': task.deadline,
        'action_url': _get_abs_url(f"/tasks/{task.id}/")
    }

    notify(
        recipient=worker,
        n_type='correspondence_issued' if is_corr else 'task_assigned',
        title=title,
        message=body,
        obj_type='task',
        obj_id=task.id,
        email_flag_name='email_on_task_assigned',
        subject=subject,
        extra_context=extra_context
    )


def notify_correspondence_assigned(correspondence, worker):
    """Notify a worker that they have been assigned an administrative correspondence."""
    deadline_str = "N/A"
    if correspondence.deadline:
        if hasattr(correspondence.deadline, 'strftime'):
            deadline_str = correspondence.deadline.strftime("%Y-%m-%d %H:%M")
        else:
            deadline_str = str(correspondence.deadline)

    corr_label = correspondence.get_correspondence_type_display() or "Correspondence"
    title = f'New {corr_label} Issued: {correspondence.title}'
    subject = f'Administrative Correspondence: {correspondence.title}'
    body = (
        f'You have been issued a new administrative {corr_label.lower()}: "{correspondence.title}".\n\n'
        f'Reference: {correspondence.reference_number or "N/A"}\n'
        f'Deadline: {deadline_str}\n\n'
        f'Action Required: Please log in to WorkTrack Pro to acknowledge receipt of this {corr_label.lower()}.'
    )

    # Append dashboard link
    dashboard_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    body += f'\n\nView Dashboard: {dashboard_url}'

    # Get absolute cover image URL
    cover_image_url = _get_abs_url(correspondence.cover_image.url) if correspondence.cover_image else None

    extra_context = {
        'status': correspondence.get_status_display(),
        'priority': correspondence.get_priority_display(),
        'progress': "0", # Correspondence doesn't have a progress field in the same way Task does
        'cover_image_url': cover_image_url,
        'deadline_obj': correspondence.deadline,
        'action_url': _get_abs_url(f"/correspondence/{correspondence.id}/")
    }

    notify(
        recipient=worker,
        n_type='correspondence_issued',
        title=title,
        message=body,
        obj_type='correspondence',
        obj_id=correspondence.id,
        email_flag_name='email_on_task_assigned',
        subject=subject,
        extra_context=extra_context
    )


def notify_submission_received(submission):
    """Notify managers that a new task submission has been received."""
    task = submission.task
    # Include the task creator and all active managers/admins
    managers = User.objects.filter(role__in=['manager', 'super_admin'], is_active=True)
    
    recipients = set(managers)
    recipients.add(task.created_by)
    
    # Get absolute cover image URL
    cover_image_url = _get_abs_url(task.cover_image.url) if task.cover_image else None
    extra_context = {
        'status': task.get_status_display(),
        'priority': task.get_priority_display(),
        'progress': str(task.progress),
        'cover_image_url': cover_image_url,
    }

    for manager in recipients:
        if manager == submission.worker:
            continue
            
        notify(
            recipient=manager,
            n_type='submission_received',
            title=f'New Submission: {task.title}',
            message=(
                f'{submission.worker.get_full_name()} has submitted work for '
                f'"{task.title}" (v{submission.version}).\n\n'
                f'Please review and approve or reject via the dashboard.'
            ),
            obj_type='submission',
            obj_id=submission.id,
            email_flag_name='submission_notifications',
            extra_context=extra_context
        )


def notify_submission_reviewed(submission):
    task = submission.task
    status_label = 'approved ✅' if submission.status == 'approved' else 'rejected ❌'
    
    # Get absolute cover image URL
    cover_image_url = _get_abs_url(task.cover_image.url) if task.cover_image else None
    extra_context = {
        'status': submission.get_status_display(),
        'priority': task.get_priority_display(),
        'progress': str(task.progress),
        'cover_image_url': cover_image_url,
    }

    notify(
        recipient=submission.worker,
        n_type='submission_approved' if submission.status == 'approved' else 'submission_rejected',
        title=f'Submission {status_label.split()[0].capitalize()}: {submission.task.title}',
        message=(
            f'Your submission for "{submission.task.title}" has been {status_label}.\n'
            f'Score: {submission.score if submission.score is not None else "N/A"}/100\n'
            + (f'Feedback: {submission.manager_feedback}' if submission.manager_feedback else '')
        ),
        obj_type='submission',
        obj_id=submission.id,
        email_flag_name='task_notifications', # Corrected flag
        extra_context=extra_context
    )


def notify_resubmission_requested(task, worker, new_sub, manager):
    """Notify worker that a manager requested a new version (resubmission)."""
    # Get absolute cover image URL
    cover_image_url = _get_abs_url(task.cover_image.url) if task.cover_image else None
    extra_context = {
        'status': task.get_status_display(),
        'priority': task.get_priority_display(),
        'progress': str(task.progress),
        'cover_image_url': cover_image_url,
    }

    notify(
        recipient=worker,
        n_type='task_assigned',
        title=f'New Version Requested: {task.title}',
        message=(
            f'Manager {manager.get_full_name()} requested a new version for "{task.title}".\n'
            f'v{new_sub.version} is now pending in your portal.\n'
            f'Please review the feedback and resubmit your work.'
        ),
        obj_type='task',
        obj_id=task.id,
        email_flag_name='task_notifications',
        extra_context=extra_context
    )


def notify_correspondence_acknowledged(submission, worker):
    """Notify managers that a worker acknowledged a correspondence."""
    task = submission.task
    managers = User.objects.filter(role__in=['manager', 'super_admin'], is_active=True).exclude(id=worker.id)
    
    # Get absolute cover image URL
    cover_image_url = _get_abs_url(task.cover_image.url) if task.cover_image else None
    extra_context = {
        'status': task.get_status_display(),
        'priority': task.get_priority_display(),
        'progress': str(task.progress),
        'cover_image_url': cover_image_url,
    }

    for manager in managers:
        notify(
            recipient=manager,
            n_type='submission_received',
            title=f'Correspondence Acknowledged: {task.title}',
            message=f'{worker.get_full_name() or worker.email} acknowledged receipt of "{task.title}".',
            obj_type='submission',
            obj_id=submission.id,
            email_flag_name='submission_notifications',
            extra_context=extra_context
        )


def notify_task_comment(comment):
    """Notify all stakeholders (creator + assigned) about a new comment, except the author."""
    task = comment.task
    recipients = set()
    recipients.add(task.created_by)
    for u in task.assigned_to.all():
        recipients.add(u)
    recipients.discard(comment.author)

    for recipient in recipients:
        # Get absolute cover image URL
        cover_image_url = _get_abs_url(task.cover_image.url) if task.cover_image else None
        extra_context = {
            'status': task.get_status_display(),
            'priority': task.get_priority_display(),
            'progress': str(task.progress),
            'cover_image_url': cover_image_url,
        }

        notify(
            recipient=recipient,
            n_type='feedback_received',
            title=f'💬 New comment on: {task.title}',
            message=(
                f'{comment.author.get_full_name()} commented on task "{task.title}":\n\n'
                f'"{comment.message}"'
            ),
            obj_type='task',
            obj_id=task.id,
            email_flag_name='task_notifications',
            extra_context=extra_context
        )
