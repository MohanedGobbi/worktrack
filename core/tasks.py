from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_notification_task(self, recipient_email, subject, message):
    """
    Celery task to send email notifications in the background.
    """
    try:
        sent_count = send_mail(
            subject=subject,
            message="Please use an HTML-capable email client to view this message.",
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Task: Email sent to {recipient_email}. Count: {sent_count}")
        return sent_count
    except Exception as e:
        logger.error(f"Task: Failed to send email to {recipient_email}: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
