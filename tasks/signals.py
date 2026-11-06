from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from tasks.models import Task
from audit.models import ActivityLog


@receiver(post_save, sender=Task)
def log_task_creation(sender, instance, created, **kwargs):
    """Log task creation."""
    if created:
        ActivityLog.objects.create(
            user=instance.created_by,
            action='create',
            object_type='Task',
            object_id=instance.id,
            object_str=instance.title,
            description=f'Task created: {instance.title}'
        )


@receiver(m2m_changed, sender=Task.assigned_to.through)
def update_task_progress_on_assignment_change(sender, instance, action, **kwargs):
    """Recalculate task progress when assigned users are added/removed."""
    if action in ["post_add", "post_remove", "post_clear"]:
        instance.recalculate_progress()
