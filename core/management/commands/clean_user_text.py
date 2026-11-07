"""Clean user text already stored before the save-time cleaning existed.

    manage.py clean_user_text            # report what would change
    manage.py clean_user_text --apply    # write the cleaned values

Uses QuerySet.update per row, so no save() side effects (signals,
notifications, timestamps) are triggered.
"""
from django.apps import apps
from django.core.management.base import BaseCommand

from core.sanitize import clean_rich, clean_text
from core.signals import CLEAN_FIELDS


class Command(BaseCommand):
    help = 'Strip HTML from stored user text (messages keep their small formatting allowlist).'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Write changes (default is a dry run).')

    def handle(self, *args, apply=False, **options):
        total = 0
        for (app_label, model_name), (plain, rich) in CLEAN_FIELDS.items():
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                continue
            names = {f.name for f in model._meta.get_fields()}
            fields = [(f, clean_text) for f in plain if f in names] + [(f, clean_rich) for f in rich if f in names]
            if not fields:
                continue
            changed = 0
            for row in model.objects.only('pk', *[f for f, _ in fields]).iterator():
                updates = {}
                for name, fn in fields:
                    old = getattr(row, name)
                    new = fn(old)
                    if new != old:
                        updates[name] = new
                if updates:
                    changed += 1
                    if apply:
                        model.objects.filter(pk=row.pk).update(**updates)
            if changed:
                self.stdout.write(f'{app_label}.{model_name}: {changed} row(s)')
            total += changed
        verb = 'Cleaned' if apply else 'Would clean'
        self.stdout.write(self.style.SUCCESS(f'{verb} {total} row(s).' + ('' if apply else ' Run with --apply to write.')))
