from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.models import Task
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process recurring tasks and reactivate them for the next cycle'

    def handle(self, *args, **options):
        now = timezone.now()
        # Find tasks that are recurring and have reached their deadline
        tasks = Task.objects.filter(is_recurring=True, deadline__lte=now)
        
        count = 0
        for task in tasks:
            try:
                # Use the centralized logic in the model
                if task.reactivate_if_needed():
                    count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'Successfully reactivated task: "{task.title}" '
                        f'(Next deadline: {task.deadline}, Remaining cycles: {task.recurrence_limit})'
                    ))
            except Exception as e:
                logger.error(f'Error reactivating task {task.id}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'Failed to reactivate task {task.id}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Process complete. Reactivated {count} recurring tasks.'))
