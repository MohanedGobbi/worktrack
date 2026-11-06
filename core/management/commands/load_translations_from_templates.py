from django.core.management.base import BaseCommand
from django.core.cache import cache
from core.models import TranslationItem
from core import views_translations
import json


class Command(BaseCommand):
    help = 'Scan templates for translatable strings and merge them into the TranslationItem table.'

    def add_arguments(self, parser):
        parser.add_argument('--restore', action='store_true', help='Clear DB and restore from templates')
        parser.add_argument('--merge', action='store_true', help='Merge missing keys from templates (default)')
        parser.add_argument('--deep-sync', action='store_true', help='Run deep sync to infer Arabic/English from templates')

    def handle(self, *args, **options):
        if not options.get('restore') and not options.get('merge') and not options.get('deep_sync'):
            options['merge'] = True

        if options.get('restore'):
            self.stdout.write('Scanning templates...')
            translations = views_translations._scan_templates_for_translations()
            if not translations:
                self.stdout.write(self.style.ERROR('No translatable strings were found in templates.'))
                return
            TranslationItem.objects.all().delete()
            objects_to_create = [TranslationItem(**entry) for entry in translations]
            TranslationItem.objects.bulk_create(objects_to_create)
            try:
                cache.delete('all_translations')
                version = cache.get('translation_cache_version', 0)
                cache.set('translation_cache_version', version + 1, timeout=None)
            except Exception:
                pass
            self.stdout.write(self.style.SUCCESS(f'Restored {len(objects_to_create)} default translations.'))
            return

        if options.get('merge'):
            self.stdout.write('Scanning templates and merging...')
            translations = views_translations._scan_templates_for_translations()
            if not translations:
                self.stdout.write(self.style.ERROR('No translatable strings were found in templates.'))
                return
            created = 0
            updated = 0
            for entry in translations:
                key = entry.get('key')
                if not key:
                    continue
                existing = TranslationItem.objects.filter(key=key).first()
                if existing:
                    template_eng = (entry.get('english_text') or '').strip()
                    template_ar = (entry.get('arabic_text') or '').strip()
                    changed = False
                    if template_eng and not (existing.english_text or '').strip():
                        existing.english_text = template_eng
                        changed = True

                    if template_ar and not (existing.arabic_text or '').strip():
                        existing.arabic_text = template_ar
                        changed = True

                    if changed:
                        existing.save()
                        updated += 1
                else:
                    TranslationItem.objects.create(**entry)
                    created += 1

            try:
                cache.delete('all_translations')
                version = cache.get('translation_cache_version', 0)
                cache.set('translation_cache_version', version + 1, timeout=None)
            except Exception:
                pass

            self.stdout.write(self.style.SUCCESS(f'Merge complete. Created: {created}, Updated: {updated}.'))

        if options.get('deep_sync'):
            self.stdout.write('Running deep sync (inference from bilingual spans)...')
            # Reuse the view's deep sync logic
            _BILINGUAL_RE = views_translations.re.compile(
                r'<span[^>]*class="lang-en"[^>]*>(.*?)</span>\s*<span[^>]*class="lang-ar"[^>]*>(.*?)</span>',
                views_translations.re.IGNORECASE | views_translations.re.DOTALL,
            )
            def _strip_tags(s):
                return views_translations.re.sub(r'<[^>]+>', '', s or '').strip()

            en_to_ar = {}
            for template_root in views_translations._get_template_dirs():
                for rt, _, files in views_translations.os.walk(template_root):
                    for fn in files:
                        if not fn.lower().endswith('.html'):
                            continue
                        try:
                            c = views_translations.open(views_translations.os.path.join(rt, fn), encoding='utf-8', errors='ignore').read()
                        except Exception:
                            continue
                        for m in _BILINGUAL_RE.finditer(c):
                            en = _strip_tags(m.group(1))
                            ar = _strip_tags(m.group(2))
                            if en and ar and len(en) >= 2:
                                en_to_ar[en.lower()] = ar

            updated_en = 0
            updated_ar = 0
            for item in TranslationItem.objects.all():
                changed = False
                en_key = (item.english_text or '').strip().lower()
                if en_key and not (item.arabic_text or '').strip():
                    ar = en_to_ar.get(en_key)
                    if ar:
                        item.arabic_text = ar
                        changed = True
                        updated_ar += 1
                if not (item.english_text or '').strip():
                    slug = views_translations.re.sub(r'^auto\.global\.', '', item.key or '')
                    slug = views_translations.re.sub(r'^auto\.[^.]+\.', '', slug)
                    readable = slug.replace('_', ' ').strip()
                    if readable and len(readable) >= 2 and not any('\u0600' <= c <= '\u06FF' for c in readable):
                        item.english_text = readable.title()
                        changed = True
                        updated_en += 1
                if changed:
                    item.save()

            try:
                cache.delete('all_translations')
                version = cache.get('translation_cache_version', 0)
                cache.set('translation_cache_version', version + 1, timeout=None)
            except Exception:
                pass

            total_both = TranslationItem.objects.exclude(english_text='').exclude(english_text__isnull=True).exclude(arabic_text='').exclude(arabic_text__isnull=True).count()
            self.stdout.write(self.style.SUCCESS(
                f'Deep sync complete. English recovered: {updated_en}, Arabic matched: {updated_ar}. Total with both: {total_both}.'
            ))
