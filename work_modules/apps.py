from django.apps import AppConfig


class WorkModulesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'work_modules'

    def ready(self):
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv or 'test' in sys.argv:
            return
        try:
            from work_modules.models import WorkModule
            WorkModule.objects.get_or_create(
                slug='contact-submissions',
                defaults={
                    'name': 'Contact Submissions',
                    'icon_class': 'fa-envelope',
                    'color': '#10b981',
                    'description': 'Special module dedicated to reviewing contact form and service request submissions.',
                    'is_private': False,
                }
            )
        except Exception:
            pass
