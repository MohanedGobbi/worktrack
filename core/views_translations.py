from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.core.cache import cache
from django.db.models import Q, Count
from django.conf import settings
from django.template.loaders.app_directories import get_app_template_dirs
from core.models import TranslationItem
from django.core.paginator import Paginator
from datetime import datetime, timezone
import json
import os
import re
import time
from collections import Counter

MIN_DATETIME = datetime.min.replace(tzinfo=timezone.utc)

BILINGUAL_SPAN_RE = re.compile(
    r'<span[^>]*class="lang-en"[^>]*>(.*?)</span>\s*<span[^>]*class="lang-ar"[^>]*>(.*?)</span>',
    re.IGNORECASE | re.DOTALL
)
TRANS_DB_RE = re.compile(
    r"""{%\s*trans_db\s+['\"](?P<key>[^'\"]+)['\"](?:\s+default\s*=\s*['\"](?P<default>[^'\"]*)['\"])?(?:\s+ctx_str\s*=\s*['\"](?P<context>[^'\"]*)['\"])?[^%]*%}""",
    re.DOTALL
)
TRANS_FILTER_RE = re.compile(
    r"""\{\{\s*['\"](?P<text>[^'\"]+)['\"]\s*\|\s*t\s*\}\}""",
    re.DOTALL
)
ATTR_TEXT_RE = re.compile(
    r'\b(?:placeholder|title|alt|aria-label|value|data-i18n-title-en|data-i18n-title-ar)\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE
)
TEXT_NODE_RE = re.compile(r'>([^<>{}%]+)<')


from core.translation_store import invalidate_unified_translation_store, get_unified_translation_store

def _invalidate_translation_cache():
    """Flushes translation cache and bumps version numbers across system."""
    invalidate_unified_translation_store()


def _normalize_page_name(context):
    if not context:
        return 'general'
    context = str(context).strip()
    if context.startswith('Found in '):
        return context[len('Found in '):].strip()
    return context


def _is_valid_template_text(value):
    if not value:
        return False
    text = str(value).strip()
    if len(text) < 2:
        return False
    if '{{' in text or '{%' in text or '}}' in text or '%}' in text:
        return False
    if text.startswith(('http://', 'https://', 'data:', 'javascript:')):
        return False
    if not any(ch.isalpha() for ch in text):
        return False
    if re.fullmatch(r'[\s\W]+', text):
        return False
    return True


def _make_auto_key(page_context, text):
    slug = re.sub(r'[^\w]+', '_', text.strip().lower()).strip('_')
    if not slug:
        slug = str(abs(hash(text)))[:10]
    return f"auto.global.{slug}"[:255]


def _extract_module(page_name):
    if not page_name or page_name == 'general':
        return 'general'
    cleaned = page_name.split('/')[0].strip()
    return cleaned or 'general'


def _extract_component(page_name):
    if not page_name or page_name == 'general':
        return 'general'
    parts = page_name.replace('\\', '/').split('/')
    if len(parts) > 1:
        return parts[-2] if parts[-2] else parts[-1]
    return os.path.splitext(parts[-1])[0] if parts else 'general'


def _source_metadata(context):
    if not context:
        return {
            'source_path': 'auto-registered',
            'file_name': 'auto-registered',
            'page': 'general',
            'component': 'general',
            'module': 'general',
        }
    normalized = context.replace('\\', '/').strip()
    file_name = os.path.basename(normalized)
    page = os.path.splitext(file_name)[0] if file_name else normalized
    module = _extract_module(normalized)
    component = _extract_component(normalized)
    return {
        'source_path': normalized,
        'file_name': file_name,
        'page': page,
        'component': component,
        'module': module,
    }


def _item_status(item):
    if not item.english_text or not item.english_text.strip():
        return 'missing_english'
    if not item.arabic_text or not item.arabic_text.strip():
        return 'missing_arabic'
    return 'translated'


def _get_template_dirs():
    template_dirs = []
    for template in settings.TEMPLATES:
        template_dirs.extend(template.get('DIRS', []))

    if getattr(settings, 'APP_DIRS', False):
        template_dirs.extend(get_app_template_dirs('django.template'))

    if not template_dirs and hasattr(settings, 'BASE_DIR'):
        template_dirs.append(os.path.join(settings.BASE_DIR, 'templates'))

    unique_dirs = []
    for d in template_dirs:
        if d and os.path.isdir(d) and d not in unique_dirs:
            unique_dirs.append(d)
    return unique_dirs


def _scan_templates_for_translations():
    entries = {}
    for template_root in _get_template_dirs():
        for root, _, files in os.walk(template_root):
            for filename in files:
                if not filename.lower().endswith('.html'):
                    continue

                full_path = os.path.join(root, filename)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception:
                    continue

                content = re.sub(r'(?s)<!--.*?-->', ' ', content)
                content = re.sub(r'(?s)<script.*?>.*?</script>', ' ', content)
                content = re.sub(r'(?s)<style.*?>.*?</style>', ' ', content)

                relative_path = os.path.relpath(full_path, template_root).replace('\\', '/')
                page_context = relative_path

                # 1. Extract bilingual spans first
                for match in BILINGUAL_SPAN_RE.finditer(content):
                    en_text = re.sub(r'<[^>]+>', '', match.group(1) or '').strip()
                    ar_text = re.sub(r'<[^>]+>', '', match.group(2) or '').strip()
                    if _is_valid_template_text(en_text) or _is_valid_template_text(ar_text):
                        key_text = en_text if en_text else ar_text
                        key = _make_auto_key(page_context, key_text)
                        if key not in entries:
                            entries[key] = {
                                'key': key,
                                'english_text': en_text,
                                'arabic_text': ar_text,
                                'context': page_context,
                            }
                # Remove bilingual spans from content to avoid double-parsing
                content = BILINGUAL_SPAN_RE.sub(' ', content)

                # 2. Extract {% trans_db %} tags
                for match in TRANS_DB_RE.finditer(content):
                    key = match.group('key').strip()
                    default = match.group('default')
                    english = default.strip() if default and default.strip() else key
                    if key and key not in entries:
                        is_ar = any('\u0600' <= char <= '\u06FF' for char in english)
                        entries[key] = {
                            'key': key,
                            'english_text': '' if is_ar else english,
                            'arabic_text': english if is_ar else '',
                            'context': page_context,
                        }

                # 3. Extract {{ "text"|t }} filters
                for match in TRANS_FILTER_RE.finditer(content):
                    text = match.group('text').strip()
                    if _is_valid_template_text(text) and text not in entries:
                        is_ar = any('\u0600' <= char <= '\u06FF' for char in text)
                        entries[text] = {
                            'key': text,
                            'english_text': '' if is_ar else text,
                            'arabic_text': text if is_ar else '',
                            'context': page_context,
                        }

                # 4. Extract translatable element attributes
                for match in ATTR_TEXT_RE.finditer(content):
                    text = match.group(1).strip()
                    if _is_valid_template_text(text):
                        key = _make_auto_key(page_context, text)
                        if key not in entries:
                            is_ar = any('\u0600' <= char <= '\u06FF' for char in text)
                            entries[key] = {
                                'key': key,
                                'english_text': '' if is_ar else text,
                                'arabic_text': text if is_ar else '',
                                'context': page_context,
                            }

                # 5. Extract HTML text nodes
                for match in TEXT_NODE_RE.finditer(content):
                    text = match.group(1).strip()
                    if _is_valid_template_text(text):
                        key = _make_auto_key(page_context, text)
                        if key not in entries:
                            is_ar = any('\u0600' <= char <= '\u06FF' for char in text)
                            entries[key] = {
                                'key': key,
                                'english_text': '' if is_ar else text,
                                'arabic_text': text if is_ar else '',
                                'context': page_context,
                            }

    return list(entries.values())


@login_required(login_url='login')
def translation_manager(request):
    if getattr(request.user, 'role', None) not in ['super_admin']:
        return render(request, 'errors/403.html', status=403)

    pages_query = request.GET.get('pages_q', '').strip()
    words_query = request.GET.get('words_q', '').strip()
    q = request.GET.get('q', '').strip() or pages_query or words_query
    pages_sort = request.GET.get('pages_sort', 'name')
    pages_status = request.GET.get('pages_status', 'all')
    pages_page = request.GET.get('pages_page')
    selected_page = request.GET.get('selected_page', 'all')
    selected_module = request.GET.get('selected_module', 'all')

    words_sort = request.GET.get('words_sort', 'updated')
    words_filter = request.GET.get('words_filter', 'all')
    words_page = request.GET.get('words_page', 1)
    try:
        per_page = int(request.GET.get('per_page', 15))
        if per_page not in [10, 15, 25, 50, 100]:
            per_page = 15
    except ValueError:
        per_page = 15

    items = list(TranslationItem.objects.all().order_by('-updated_at'))

    active_keys = cache.get('translation_active_keys')
    if active_keys is None:
        active_keys = set(entry['key'] for entry in _scan_templates_for_translations())
        cache.set('translation_active_keys', active_keys, 300)

    for item in items:
        item.source = _source_metadata(item.context)
        item.page_name = item.source['page']
        item.module = item.source['module']
        item.component = item.source['component']
        item.file_name = item.source['file_name']
        item.source_path = item.source['source_path']
        item.status = _item_status(item)
        if item.key not in active_keys and item.status == 'translated':
            item.status = 'unused'

    total_count = len(items)
    total_translated = len([item for item in items if item.status == 'translated'])
    total_missing_ar = len([item for item in items if item.status == 'missing_arabic'])
    total_missing_en = len([item for item in items if item.status == 'missing_english'])

    page_stats = {}
    for item in items:
        page = item.page_name
        stats = page_stats.setdefault(page, {
            'name': page,
            'module': _extract_module(page),
            'total': 0,
            'translated': 0,
            'missing_arabic': 0,
            'missing_english': 0,
            'last_updated': item.updated_at,
        })
        stats['total'] += 1
        if item.status == 'translated':
            stats['translated'] += 1
        if item.status == 'missing_arabic':
            stats['missing_arabic'] += 1
        if item.status == 'missing_english':
            stats['missing_english'] += 1
        if item.updated_at and (stats['last_updated'] is None or item.updated_at > stats['last_updated']):
            stats['last_updated'] = item.updated_at

    pages = []
    for page_name, stats in page_stats.items():
        stats['completion'] = int((stats['translated'] / stats['total']) * 100) if stats['total'] else 0
        pages.append(stats)

    if q:
        filter_text = q.lower()
        pages = [page for page in pages if filter_text in (page['name'] or '').lower() or filter_text in (page['module'] or '').lower()]

    if pages_status == 'translated':
        pages = [page for page in pages if page['translated'] == page['total']]
    elif pages_status == 'incomplete':
        pages = [page for page in pages if page['translated'] < page['total']]

    if pages_sort == 'total':
        pages.sort(key=lambda x: x['total'], reverse=True)
    elif pages_sort == 'translated':
        pages.sort(key=lambda x: x['translated'], reverse=True)
    elif pages_sort == 'missing':
        pages.sort(key=lambda x: x['missing_arabic'] + x['missing_english'], reverse=True)
    elif pages_sort == 'updated':
        pages.sort(key=lambda x: x['last_updated'] or MIN_DATETIME, reverse=True)
    else:
        pages.sort(key=lambda x: (x['name'] or '').lower())

    pages_paginator = Paginator(pages, 5)
    pages_page_obj = pages_paginator.get_page(pages_page)

    words = items
    if selected_module != 'all':
        words = [item for item in words if item.module == selected_module]

    if selected_page != 'all':
        words = [item for item in words if item.page_name == selected_page]

    if q:
        q_lower = q.lower()
        words = [
            item for item in words
            if q_lower in (item.key or '').lower()
            or q_lower in (item.english_text or '').lower()
            or q_lower in (item.arabic_text or '').lower()
            or q_lower in (getattr(item, 'page_name', '') or '').lower()
            or q_lower in (getattr(item, 'module', '') or '').lower()
        ]

    if words_filter == 'missing_arabic':
        words = [item for item in words if item.status == 'missing_arabic']
    elif words_filter == 'missing_english':
        words = [item for item in words if item.status == 'missing_english']
    elif words_filter == 'translated':
        words = [item for item in words if item.status == 'translated']
    elif words_filter == 'empty':
        words = [item for item in words if not (item.english_text and item.english_text.strip()) or not (item.arabic_text and item.arabic_text.strip())]

    if words_sort == 'key':
        words.sort(key=lambda x: (x.key or '').lower())
    elif words_sort == 'english':
        words.sort(key=lambda x: (x.english_text or '').lower())
    elif words_sort == 'arabic':
        words.sort(key=lambda x: (x.arabic_text or '').lower())
    else:
        words.sort(key=lambda x: (x.updated_at or MIN_DATETIME, x.id), reverse=True)

    selected_page_items = [item for item in items if selected_page == 'all' or item.page_name == selected_page]
    selected_page_total = len(selected_page_items)
    selected_page_translated = len([item for item in selected_page_items if item.status == 'translated'])
    selected_page_missing_ar = len([item for item in selected_page_items if item.status == 'missing_arabic'])
    selected_page_missing_en = len([item for item in selected_page_items if item.status == 'missing_english'])

    words_paginator = Paginator(words, per_page)
    words_page_obj = words_paginator.get_page(words_page)

    try:
        words_page_range = words_paginator.get_elided_page_range(words_page_obj.number, on_each_side=1, on_ends=1)
    except Exception:
        words_page_range = words_paginator.page_range

    modules = sorted(set(item.module for item in items))
    pages_list = sorted(set(item.page_name for item in items))

    context = {
        'pages_page_obj': pages_page_obj,
        'words_page_obj': words_page_obj,
        'words_page_range': words_page_range,
        'pages_query': pages_query,
        'pages_sort': pages_sort,
        'pages_status': pages_status,
        'selected_page': selected_page,
        'words_query': words_query,
        'words_sort': words_sort,
        'words_filter': words_filter,
        'search_query': q,
        'per_page': per_page,
        'total_count': total_count,
        'total_translated': total_translated,
        'total_missing_ar': total_missing_ar,
        'total_missing_en': total_missing_en,
        'total_with_arabic': total_translated,
        'total_missing': total_missing_ar,
        'total_pages': len(pages),
        'total_modules': len(modules),
        'modules': modules,
        'pages_list': pages_list,
        'completion_percent': int((total_translated / total_count) * 100) if total_count else 0,
        'selected_page_total': selected_page_total,
        'selected_page_translated': selected_page_translated,
        'selected_page_missing_ar': selected_page_missing_ar,
        'selected_page_missing_en': selected_page_missing_en,
        'filtered_words_count': len(words),
        'selected_module': selected_module,
    }
    return render(request, 'pages/translation_manager.html', context)


@login_required(login_url='login')
@require_POST
def api_update_translation(request):
    if getattr(request.user, 'role', None) not in ['super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
        
    try:
        data = json.loads(request.body)
        item_id = data.get('id')
        en_text = data.get('english_text')
        ar_text = data.get('arabic_text')
        
        item = TranslationItem.objects.get(id=item_id)
        item.english_text = en_text
        item.arabic_text = ar_text
        item.save()
        _invalidate_translation_cache()
        
        return JsonResponse({'status': 'success', 'message': 'Translation updated successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url='login')
@require_POST
def api_bulk_update_translations(request):
    if getattr(request.user, 'role', None) not in ['super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        updated = 0
        for payload in items:
            item_id = payload.get('id')
            en_text = payload.get('english_text', '')
            ar_text = payload.get('arabic_text', '')
            if not item_id:
                continue
            item = TranslationItem.objects.filter(id=item_id).first()
            if not item:
                continue
            if (item.english_text or '') != en_text or (item.arabic_text or '') != ar_text:
                item.english_text = en_text
                item.arabic_text = ar_text
                item.save()
                updated += 1
        
        if updated > 0:
            _invalidate_translation_cache()

        return JsonResponse({'status': 'success', 'updated': updated, 'message': f'Successfully updated {updated} translation entries.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required(login_url='login')
@require_POST
def api_manage_translations(request):
    if getattr(request.user, 'role', None) not in ['super_admin']:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
        action = data.get('action')

        if action in ['reload', 'reload_cache']:
            _invalidate_translation_cache()
            return JsonResponse({'status': 'success', 'message': 'Active translation cache reloaded successfully.'})

        if action in ['scan', 'scan_sync', 'merge']:
            translations = _scan_templates_for_translations()
            if not translations:
                return JsonResponse({'status': 'error', 'message': 'No translatable strings were found in templates.'}, status=400)

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

                    # Only populate if existing is empty; never overwrite existing non-empty user translations
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

            _invalidate_translation_cache()
            return JsonResponse({
                'status': 'success', 
                'created': created,
                'updated': updated,
                'message': f'Scan & Sync complete! Created: {created} new strings, Updated: {updated} existing entries.'
            })

        if action == 'clear':
            TranslationItem.objects.all().delete()
            _invalidate_translation_cache()
            return JsonResponse({'status': 'success', 'message': 'All translation entries removed.'})

        if action == 'restore':
            translations = _scan_templates_for_translations()
            if not translations:
                return JsonResponse({'status': 'error', 'message': 'No translatable strings were found in templates.'}, status=400)

            TranslationItem.objects.all().delete()
            objects_to_create = [TranslationItem(**entry) for entry in translations]
            TranslationItem.objects.bulk_create(objects_to_create)
            _invalidate_translation_cache()

            return JsonResponse({'status': 'success', 'message': f'Restored {len(objects_to_create)} default translations.'})

        if action == 'dedupe':
            duplicates = TranslationItem.objects.values('english_text').annotate(cnt=Count('id')).filter(cnt__gt=1).exclude(english_text__isnull=True).exclude(english_text='')
            merged_groups = 0
            merged_rows = 0
            for dup in duplicates:
                en = dup['english_text']
                items_qs = TranslationItem.objects.filter(english_text=en).order_by('-updated_at', '-id')
                items = list(items_qs)
                if len(items) < 2:
                    continue
                keep = items[0]
                others = items[1:]
                changed = False
                for o in others:
                    if (not keep.english_text or not keep.english_text.strip()) and (o.english_text and o.english_text.strip()):
                        keep.english_text = o.english_text
                        changed = True
                    if (not keep.arabic_text or not keep.arabic_text.strip()) and (o.arabic_text and o.arabic_text.strip()):
                        keep.arabic_text = o.arabic_text
                        changed = True
                    if o.updated_at and (not keep.updated_at or o.updated_at > keep.updated_at):
                        keep.updated_at = o.updated_at
                        changed = True
                    o.delete()
                    merged_rows += 1
                if changed:
                    keep.save()
                merged_groups += 1

            _invalidate_translation_cache()
            return JsonResponse({'status': 'success', 'message': f'Deduplicated {merged_groups} text groups, removed {merged_rows} duplicate rows.'})

        if action == 'clean_arabic':
            from core.clean_arabic_translations import clean_arabic_text
            cleaned_count = 0
            for item in TranslationItem.objects.all():
                ar = item.arabic_text or ''
                if re.search(r'[a-zA-Z]{2,}', ar):
                    new_ar = clean_arabic_text(item.english_text, ar, item.key)
                    new_ar = re.sub(r'[a-zA-Z]+', '', new_ar).strip()
                    new_ar = re.sub(r'\s+', ' ', new_ar).strip()
                    item.arabic_text = new_ar or 'توطين النظام'
                    item.save()
                    cleaned_count += 1
            _invalidate_translation_cache()
            return JsonResponse({'status': 'success', 'message': f'Cleaned and Arabicized {cleaned_count} translation entries.'})

        if action == 'deep_sync':
            _BILINGUAL_RE = re.compile(
                r'<span[^>]*class="lang-en"[^>]*>(.*?)</span>\s*<span[^>]*class="lang-ar"[^>]*>(.*?)</span>',
                re.IGNORECASE | re.DOTALL,
            )
            def _strip_tags(s):
                return re.sub(r'<[^>]+>', '', s or '').strip()

            def _has_arabic(s):
                return any('\u0600' <= c <= '\u06FF' for c in (s or ''))

            en_to_ar = {}
            for template_root in _get_template_dirs():
                for rt, _, files in os.walk(template_root):
                    for fn in files:
                        if not fn.lower().endswith('.html'):
                            continue
                        try:
                            c = open(os.path.join(rt, fn), encoding='utf-8', errors='ignore').read()
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
                    slug = re.sub(r'^auto\.global\.', '', item.key or '')
                    slug = re.sub(r'^auto\.[^.]+\.', '', slug)
                    readable = slug.replace('_', ' ').strip()
                    if readable and len(readable) >= 2 and not _has_arabic(readable):
                        item.english_text = readable.title()
                        changed = True
                        updated_en += 1
                if changed:
                    item.save()

            _invalidate_translation_cache()

            total_both = TranslationItem.objects.exclude(english_text='').exclude(english_text__isnull=True)\
                .exclude(arabic_text='').exclude(arabic_text__isnull=True).count()
            return JsonResponse({'status': 'success', 'message': (
                f'Deep sync complete! '
                f'English recovered: {updated_en}, Arabic matched: {updated_ar}. '
                f'Total entries with both languages: {total_both}.'
            )})

        if action == 'export':
            items = TranslationItem.objects.all().order_by('key')
            rows = []
            for item in items:
                rows.append({
                    'key': item.key,
                    'english_text': item.english_text or '',
                    'arabic_text': item.arabic_text or '',
                    'context': item.context or '',
                    'status': _item_status(item),
                    'module': _extract_module(_normalize_page_name(item.context)),
                    'page': _normalize_page_name(item.context),
                })
            return JsonResponse({'status': 'success', 'translations': rows})

        if action == 'import':
            translations = data.get('translations') or []
            if not isinstance(translations, list) or not translations:
                return JsonResponse({'status': 'error', 'message': 'No translations payload was provided.'}, status=400)
            created = 0
            updated = 0
            for entry in translations:
                key = entry.get('key')
                if not key:
                    continue
                en_text = entry.get('english_text', '').strip()
                ar_text = entry.get('arabic_text', '').strip()
                context = entry.get('context', '').strip() or 'imported'
                item = TranslationItem.objects.filter(key=key).first()
                if item:
                    if item.english_text != en_text or item.arabic_text != ar_text or item.context != context:
                        item.english_text = en_text
                        item.arabic_text = ar_text
                        item.context = context
                        item.save()
                        updated += 1
                else:
                    TranslationItem.objects.create(
                        key=key,
                        english_text=en_text,
                        arabic_text=ar_text,
                        context=context,
                    )
                    created += 1
            _invalidate_translation_cache()
            return JsonResponse({'status': 'success', 'created': created, 'updated': updated, 'message': f'Import complete! Created: {created}, Updated: {updated}.'})

        return JsonResponse({'status': 'error', 'message': 'Unknown action.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@require_GET
def api_translation_map(request):
    """Return translation map from database for the frontend language picker."""
    try:
        store = get_unified_translation_store()
        response = JsonResponse(store['map_json'])
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
