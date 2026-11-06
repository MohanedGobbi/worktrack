from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser, UserProfile
from notifications.models import NotificationPreference


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a user profile when a new user is created."""
    if created:
        UserProfile.objects.create(user=instance)
        NotificationPreference.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Save the user profile when the user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
