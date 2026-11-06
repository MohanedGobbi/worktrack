import os
import re
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db.models import Count
from core.views_translations import _scan_templates_for_translations, _get_template_dirs
from core.models import TranslationItem

TRANSLATION_CACHE_VERSION_KEY = 'translation_cache_version'
TRANSLATION_TIMESTAMP_FILE = '/tmp/translation_last_updated.txt'


def _touch_translation_version():
    try:
        version = cache.get(TRANSLATION_CACHE_VERSION_KEY, 0) or 0
        cache.set(TRANSLATION_CACHE_VERSION_KEY, version + 1, timeout=None)
    except Exception:
        pass
    try:
        with open(TRANSLATION_TIMESTAMP_FILE, 'w', encoding='utf-8') as f:
            f.write(str(version + 1))
    except Exception:
        pass


def _strip_tags(text):
    return re.sub(r'<[^>]+>', '', text or '').strip()


def _has_arabic(text):
    return any('\u0600' <= ch <= '\u06FF' for ch in (text or ''))


def _scan_bilingual_pairs():
    en_to_ar = {}
    for template_root in _get_template_dirs():
        for root, _, files in os.walk(template_root):
            for filename in files:
                if not filename.lower().endswith('.html'):
                    continue
                try:
                    with open(os.path.join(root, filename), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception:
                    continue
                for match in re.finditer(r'<span[^>]*class=["\']lang-en["\'][^>]*>(.*?)</span>\s*<span[^>]*class=["\']lang-ar["\'][^>]*>(.*?)</span>', content, re.IGNORECASE | re.DOTALL):
                    en_text = _strip_tags(match.group(1))
                    ar_text = _strip_tags(match.group(2))
                    if en_text and ar_text:
                        en_to_ar[en_text.strip().lower()] = ar_text
    return en_to_ar


def _make_readable_from_key(key):
    slug = re.sub(r'^auto\.global\.', '', key or '')
    slug = re.sub(r'^auto\.[^.]+\.', '', slug)
    slug = slug.replace('.', ' ').replace('_', ' ').strip()
    if not slug:
        return None
    return slug.title()


class Command(BaseCommand):
    help = 'Restore all translations from templates, deep sync bilingual pairs, and clear translation caches.'

    def handle(self, *args, **options):
        self.stdout.write('Scanning templates for translation strings...')
        translations = _scan_templates_for_translations()
        if not translations:
            self.stdout.write(self.style.ERROR('No translatable strings found in templates.'))
            return

        self.stdout.write(f'Restored {len(translations)} translation entries.')
        TranslationItem.objects.all().delete()
        TranslationItem.objects.bulk_create([TranslationItem(**entry) for entry in translations])

        self.stdout.write('Running deep sync against bilingual spans...')
        bilingual_map = _scan_bilingual_pairs()
        updated_ar = 0
        updated_en = 0

        for item in TranslationItem.objects.all():
            changed = False
            eng = (item.english_text or '').strip()
            ar = (item.arabic_text or '').strip()
            if eng and not ar:
                ar_match = bilingual_map.get(eng.lower())
                if ar_match:
                    item.arabic_text = ar_match
                    changed = True
                    updated_ar += 1
            if not eng:
                readable = _make_readable_from_key(item.key)
                if readable and not _has_arabic(readable):
                    item.english_text = readable
                    changed = True
                    updated_en += 1
            if changed:
                item.save()

        self.stdout.write(f'Deep sync updated Arabic: {updated_ar}, English: {updated_en}')

        self.stdout.write('Removing duplicate translations...')
        merged_groups = 0
        merged_rows = 0
        duplicates = TranslationItem.objects.values('english_text').annotate(cnt=Count('id')).filter(cnt__gt=1).exclude(english_text__isnull=True).exclude(english_text='')
        for dup in duplicates:
            items = list(TranslationItem.objects.filter(english_text=dup['english_text']).order_by('-updated_at', '-id'))
            if len(items) < 2:
                continue
            keep = items[0]
            for other in items[1:]:
                if not keep.arabic_text and other.arabic_text:
                    keep.arabic_text = other.arabic_text
                other.delete()
                merged_rows += 1
            keep.save()
            merged_groups += 1

        _touch_translation_version()
        self.stdout.write(self.style.SUCCESS(f'Rebuild complete. Duplicates removed: {merged_rows}, groups merged: {merged_groups}'))
