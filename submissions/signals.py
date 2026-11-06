from django.db.models.signals import post_save
from django.dispatch import receiver
from submissions.models import Submission
from audit.models import ActivityLog
from notifications.models import Notification
from core.email_notifications import notify_submission_received


@receiver(post_save, sender=Submission)
def log_submission(sender, instance, created, **kwargs):
    """Log submission creation and updates."""
    if created:
        action = 'submit'
        message = f'Submission created for task: {instance.task.title}'
    else:
        action = 'update'
        message = f'Submission updated for task: {instance.task.title}'
    
    ActivityLog.objects.create(
        user=instance.worker,
        action=action,
        object_type='Submission',
        object_id=instance.id,
        object_str=str(instance),
        description=message
    )


@receiver(post_save, sender=Submission)
def notify_on_submission_status_change(sender, instance, created, **kwargs):
    """Send notifications when submission status changes."""
    if instance.status == 'submitted':
        # Notify managers
        notify_submission_received(instance)
@receiver(post_save, sender=Submission)
def update_task_progress_on_submission_save(sender, instance, **kwargs):
    """Ensure the collective task progress is recalculated when any submission changes."""
    if instance.task:
        instance.task.recalculate_progress()
        instance.task.save(update_fields=['progress', 'status'])
