from django.core.management.base import BaseCommand
from core.faculty_seeder import reset_and_seed_faculty


class Command(BaseCommand):
    help = "Resets the database, leaving 1 super admin and contact module, and seeds the Faculty of Law & Political Science data"

    def add_arguments(self, parser):
        parser.add_argument(
            '--empty',
            action='store_true',
            help='Only wipe data, leave 1 admin and contact module without seeding new faculty data',
        )

    def handle(self, *args, **options):
        empty_only = options.get('empty', False)
        self.stdout.write(self.style.WARNING("Starting database reset..."))
        result = reset_and_seed_faculty(empty_only=empty_only)
        if result.get("success"):
            self.stdout.write(self.style.SUCCESS(f"Successfully finished: {result.get('message')}"))
        else:
            self.stdout.write(self.style.ERROR(f"Reset failed: {result.get('error')}"))
