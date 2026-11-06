from django.db.models.signals import post_save
from django.dispatch import receiver
from kpi.models import UserKPI, KPIWeight
from submissions.models import Submission


@receiver(post_save, sender=Submission)
def recalculate_kpi_on_submission(sender, instance, **kwargs):
    """Recalculate user KPI when submission is reviewed."""
    if instance.status == 'approved' and instance.reviewed_at:
        # Trigger KPI recalculation (simplified - will be expanded)
        pass
