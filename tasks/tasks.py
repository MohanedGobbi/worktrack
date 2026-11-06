from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task(name="tasks.tasks.process_recurring_tasks_periodic")
def process_recurring_tasks_periodic():
    """
    Periodic task to trigger the process_recurring_tasks management command.
    """
    try:
        logger.info("Starting periodic recurrence processing...")
        call_command('process_recurring_tasks')
        logger.info("Periodic recurrence processing completed successfully.")
    except Exception as e:
        logger.error(f"Error in periodic recurrence processing: {str(e)}")
