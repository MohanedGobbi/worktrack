"""
Management command: check_deadlines
Run periodically (e.g. via cron every 15 min) to:
  - Auto-mark overdue tasks
  - Send deadline reminder notifications (48h, 24h, 1h windows)

Usage:
  python manage.py check_deadlines
Cron example (every 15 minutes):
  */15 * * * * /path/to/venv/bin/python /path/to/manage.py check_deadlines
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from notifications.models import Notification
from django.core.mail import send_mail
from django.conf import settings


def _create_notification(recipient, n_type, title, message, obj_type='task', obj_id=None):
    from core.email_notifications import notify
    notify(
        recipient=recipient,
        n_type=n_type,
        title=title,
        message=message,
        obj_type=obj_type,
        obj_id=obj_id,
        email_flag_name='task_notifications', # Deadlines are task-related
    )


class Command(BaseCommand):
    help = 'Auto-mark overdue tasks and send deadline reminder notifications'

    def handle(self, *args, **options):
        now = timezone.now()

        # ── 1. Mark overdue tasks ──────────────────────────────────────
        active_statuses = ['pending', 'in_progress', 'submitted']
        overdue_qs = Task.objects.filter(
            deadline__lt=now,
            status__in=active_statuses,
        )
        overdue_count = 0
        for task in overdue_qs:
            task.status = 'overdue'
            task.save(update_fields=['status', 'updated_at'])
            overdue_count += 1
            # Notify creator
            _create_notification(
                recipient=task.created_by,
                n_type='deadline_reminder',
                title=f'⚠️ Task Overdue: {task.title}',
                message=f'The task "{task.title}" has passed its deadline and is now marked overdue.',
                obj_id=task.id,
            )
            # Notify assigned workers
            for worker in task.assigned_to.all():
                _create_notification(
                    recipient=worker,
                    n_type='deadline_reminder',
                    title=f'⚠️ Task Overdue: {task.title}',
                    message=f'The task "{task.title}" is overdue. Please submit your work as soon as possible.',
                    obj_id=task.id,
                )

        self.stdout.write(f'[check_deadlines] Marked {overdue_count} tasks as overdue.')

        # ── 2. Deadline reminders (48h, 24h, 1h windows) ──────────────
        reminder_windows = [
            (timedelta(hours=48), timedelta(hours=47), '48 hours'),
            (timedelta(hours=24), timedelta(hours=23), '24 hours'),
            (timedelta(hours=1),  timedelta(minutes=45), '1 hour'),
        ]

        reminder_count = 0
        upcoming_qs = Task.objects.filter(status__in=['pending', 'in_progress'])

        for upper, lower, label in reminder_windows:
            window_tasks = upcoming_qs.filter(
                deadline__lte=now + upper,
                deadline__gt=now + lower,
            )
            for task in window_tasks:
                for worker in task.assigned_to.all():
                    # Avoid duplicate notifications: check if one already exists in last 30min
                    already_sent = Notification.objects.filter(
                        recipient=worker,
                        related_object_id=task.id,
                        related_object_type='task',
                        notification_type='deadline_reminder',
                        created_at__gte=now - timedelta(minutes=30),
                    ).exists()
                    if not already_sent:
                        _create_notification(
                            recipient=worker,
                            n_type='deadline_reminder',
                            title=f'⏰ Deadline in {label}: {task.title}',
                            message=f'Your task "{task.title}" is due in {label}. Make sure to submit before the deadline.',
                            obj_id=task.id,
                        )
                        reminder_count += 1

        self.stdout.write(f'[check_deadlines] Sent {reminder_count} deadline reminders.')
        self.stdout.write(self.style.SUCCESS('check_deadlines complete.'))
