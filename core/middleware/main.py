import os
import re
import time
import html
import json
import logging
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from core.models import AllowedHost, BlockedHostAttempt, TranslationItem

TRANSLATION_TIMESTAMP_FILE = '/tmp/translation_last_updated.txt'

logger = logging.getLogger(__name__)

class DynamicHostMiddleware:
    """
    Checks the Host header of every incoming request against the AllowedHost database table.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        host_header = request.META.get('HTTP_HOST', '')
        host = host_header.split(':')[0].lower()
        
        if host in ['localhost', '127.0.0.1', 'testserver', '']:
            return self.get_response(request)
            
        cache_key = f"allowed_host_{host}"
        is_allowed = cache.get(cache_key)
        
        if is_allowed is None:
            wildcard_active = cache.get('allowed_host_wildcard')
            if wildcard_active is None:
                wildcard_active = AllowedHost.objects.filter(hostname='*', is_active=True).exists()
                cache.set('allowed_host_wildcard', wildcard_active, 300)
            
            if wildcard_active:
                return self.get_response(request)
            
            is_allowed = AllowedHost.objects.filter(hostname=host, is_active=True).exists()
            cache.set(cache_key, is_allowed, 300)
            
        if not is_allowed:
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip_address:
                ip_address = ip_address.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
                
            attempt, created = BlockedHostAttempt.objects.get_or_create(
                hostname=host,
                defaults={'ip_address': ip_address}
            )
            
            if not created:
                attempt.attempt_count += 1
                if ip_address and attempt.ip_address != ip_address:
                    attempt.ip_address = ip_address
                attempt.save()
                
            return HttpResponseForbidden("<h1>403 Forbidden</h1><p>This host is not authorized to access the system.</p>")
            
        return self.get_response(request)


_MIDDLEWARE_TRANS_CACHE = {
    'by_en_norm': {},
    'mtime': -1,
    'loaded_at': 0,
}
TRANS_CACHE_TTL = 2  # seconds — reload from DB at most every 2 seconds

def _get_cache_version():
    try:
        return cache.get('translation_cache_version', 0) or 0
    except Exception:
        pass
    return 0


def _get_file_version():
    try:
        if os.path.exists(TRANSLATION_TIMESTAMP_FILE):
            with open(TRANSLATION_TIMESTAMP_FILE, 'r', encoding='utf-8') as f:
                value = f.read().strip()
            return float(value) if value else 0
    except Exception:
        pass
    return 0


def _get_translation_version():
    return max(_get_cache_version(), _get_file_version())


def _normalize_key_or_text(val):
    if not val:
        return []
    s = str(val).strip().lower()
    if not s:
        return []
    keys = [s]
    slug = re.sub(r'[^\w]+', '_', s).strip('_')
    if slug and slug not in keys:
        keys.append(slug)
    readable = slug.replace('_', ' ')
    if readable and readable not in keys:
        keys.append(readable)
    return keys


def _extract_slug_from_key(key):
    if not key:
        return []
    k = key.lower()
    keys = [k]
    if '.' in k:
        parts = k.split('.')
        last_part = parts[-1]
        if last_part and last_part not in keys:
            keys.append(last_part)
            readable = last_part.replace('_', ' ')
            if readable and readable not in keys:
                keys.append(readable)
    return keys


from core.translation_store import get_unified_translation_store, lookup_unified_translation

def get_active_translations_maps():
    store = get_unified_translation_store()
    return store['by_en_norm']


def _lookup_translation(raw_text, trans_map=None):
    return lookup_unified_translation(raw_text)


class DynamicTranslationMiddleware:
    """
    Safely updates bilingual spans (<span class="lang-en"> and <span class="lang-ar">)
    in rendered HTML responses live from database edits for BOTH English and Arabic.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only process 200 OK HTML responses
        if response.status_code != 200:
            return response
        content_type = response.get('Content-Type', '')
        if 'text/html' not in content_type:
            return response

        path = request.path_info
        # Skip translation management UI and API responses
        if path.startswith('/translations/') or path.startswith('/api/'):
            return response

        lang = request.GET.get('lang') or request.GET.get('language') or request.COOKIES.get('worktrack_lang') or request.COOKIES.get('django_language') or 'en'
        trans_map = get_active_translations_maps()
        if not trans_map and not path.startswith('/admin/'):
            return response

        try:
            content = response.content.decode('utf-8', errors='ignore')
        except Exception:
            return response

        modified = False

        # Inject server-side lang and dir attributes on <html> element for instant CSS/RTL rendering
        if lang == 'ar':
            def _inject_html_ar(m):
                nonlocal modified
                attrs = m.group(1)
                if 'lang=' in attrs:
                    attrs = re.sub(r'lang=["\'][^"\']*["\']', 'lang="ar"', attrs)
                else:
                    attrs += ' lang="ar"'
                if 'dir=' in attrs:
                    attrs = re.sub(r'dir=["\'][^"\']*["\']', 'dir="rtl"', attrs)
                else:
                    attrs += ' dir="rtl"'
                if 'class=' not in attrs:
                    attrs += ' class="rtl-mode"'
                elif 'rtl-mode' not in attrs:
                    attrs = re.sub(r'class=["\']([^"\']*)["\']', r'class="\1 rtl-mode"', attrs)
                modified = True
                return f'<html{attrs}>'
            content = re.sub(r'<html([^>]*)>', _inject_html_ar, content, count=1, flags=re.IGNORECASE)
        else:
            def _inject_html_en(m):
                nonlocal modified
                attrs = m.group(1)
                if 'lang=' in attrs:
                    attrs = re.sub(r'lang=["\'][^"\']*["\']', 'lang="en"', attrs)
                if 'dir=' in attrs:
                    attrs = re.sub(r'dir=["\'][^"\']*["\']', 'dir="ltr"', attrs)
                attrs = re.sub(r'\s*rtl-mode\b', '', attrs)
                modified = True
                return f'<html{attrs}>'
            content = re.sub(r'<html([^>]*)>', _inject_html_en, content, count=1, flags=re.IGNORECASE)

        # Protection storage for already-processed blocks and spans
        protected = []
        def _store_protected(block):
            protected.append(block)
            return f'__TRANS_PROTECT_{len(protected)-1}__'

        # 1. Protect script, style, textarea, svg, and code elements
        def _protect_raw_block(match):
            return _store_protected(match.group(0))

        content = re.sub(r'<(script|style|svg|code|pre)[^>]*>.*?</\1>', _protect_raw_block, content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<textarea[^>]*>.*?</textarea>', _protect_raw_block, content, flags=re.DOTALL | re.IGNORECASE)
        # Elements marked translate="no" (shortcuts, formulas, codes) keep their text as written
        content = re.sub(r'<(kbd|div|span|code|b|strong)\b[^>]*\btranslate="no"[^>]*>.*?</\1>', _protect_raw_block, content, flags=re.DOTALL | re.IGNORECASE)
        # Protect font icon elements (material-symbols-outlined, material-icons, fa, bi) from text node translation
        content = re.sub(r'<(span|i)[^>]*class="[^"]*(material-symbols-outlined|material-icons|fa|fab|fas|far|bi)[^"]*"[^>]*>.*?</\1>', _protect_raw_block, content, flags=re.DOTALL | re.IGNORECASE)

        # 2. Process and protect paired bilingual spans first
        def replace_bilingual_span(match):
            nonlocal modified
            raw_en = match.group(1)
            raw_ar = match.group(2)
            
            # A template that writes both languages is authoritative. Only human-written rows
            # (not the machine-generated "auto." ones) may override it, and only matched on English.
            entry = _lookup_translation(raw_en, trans_map)
            if entry and str(entry.get('key', '')).startswith('auto.'):
                entry = None
            new_en = raw_en.strip()
            new_ar = raw_ar.strip()
            if entry:
                db_en = entry.get('en')
                db_ar = entry.get('ar')
                if db_en and db_en.strip().lower() != raw_en.strip().lower():
                    new_en = db_en
                if db_ar:
                    new_ar = db_ar
                if new_en != raw_en.strip() or new_ar != raw_ar.strip():
                    modified = True
            
            result = f'<span class="lang-en">{new_en}</span><span class="lang-ar">{new_ar}</span>'
            return _store_protected(result)

        pattern_pair = r'<span[^>]*class="lang-en"[^>]*>(.*?)</span>\s*<span[^>]*class="lang-ar"[^>]*>(.*?)</span>'
        content = re.sub(pattern_pair, replace_bilingual_span, content, flags=re.DOTALL | re.IGNORECASE)

        # 3. Process standalone single lang-en spans
        def replace_single_en_span(match):
            nonlocal modified
            raw_text = match.group(1)
            entry = _lookup_translation(raw_text, trans_map)
            db_en = raw_text.strip()
            db_ar = ''
            if entry:
                if entry.get('en'):
                    db_en = entry.get('en')
                if entry.get('ar'):
                    db_ar = entry.get('ar')
            
            if db_ar:
                modified = True
                result = f'<span class="lang-en">{db_en}</span><span class="lang-ar">{db_ar}</span>'
            else:
                if db_en != raw_text.strip():
                    modified = True
                result = f'<span class="lang-en">{db_en}</span>'
            return _store_protected(result)

        pattern_single_en = r'<span[^>]*class="lang-en"[^>]*>(.*?)</span>'
        content = re.sub(pattern_single_en, replace_single_en_span, content, flags=re.DOTALL | re.IGNORECASE)

        # 4. Process standalone single lang-ar spans
        def replace_single_ar_span(match):
            nonlocal modified
            raw_text = match.group(1)
            entry = _lookup_translation(raw_text, trans_map)
            db_ar = raw_text.strip()
            db_en = ''
            if entry:
                if entry.get('ar'):
                    db_ar = entry.get('ar')
                if entry.get('en'):
                    db_en = entry.get('en')
            
            if db_en:
                modified = True
                result = f'<span class="lang-en">{db_en}</span><span class="lang-ar">{db_ar}</span>'
            else:
                if db_ar != raw_text.strip():
                    modified = True
                result = f'<span class="lang-ar">{db_ar}</span>'
            return _store_protected(result)

        pattern_single_ar = r'<span[^>]*class="lang-ar"[^>]*>(.*?)</span>'
        content = re.sub(pattern_single_ar, replace_single_ar_span, content, flags=re.DOTALL | re.IGNORECASE)

        # 5. Translatable attributes (placeholder, title, alt, aria-label)
        def replace_attr_text(match):
            nonlocal modified
            attr_name = match.group(1)
            quote = match.group(2)
            val = match.group(3)
            if val and len(val.strip()) >= 2:
                entry = _lookup_translation(val, trans_map)
                if entry:
                    db_val = entry.get(lang) or entry.get('en')
                    if db_val and db_val != val:
                        modified = True
                        return f'{attr_name}={quote}{html.escape(db_val)}{quote}'
            return match.group(0)

        pattern_attr = r'\b(placeholder|title|alt|aria-label)\s*=\s*(["\'])(.*?)\2'
        content = re.sub(pattern_attr, replace_attr_text, content, flags=re.IGNORECASE)

        # 6. Process HTML text nodes in Admin pages or non-span HTML blocks
        if trans_map:
            def replace_text_node(match):
                nonlocal modified
                prefix = match.group(1)
                text = match.group(2)
                suffix = match.group(3)
                clean_text = text.strip()
                if clean_text and len(clean_text) >= 2 and any(c.isalpha() for c in clean_text):
                    entry = _lookup_translation(clean_text, trans_map)
                    if entry:
                        target = entry.get(lang) or entry.get('en')
                        if target and target != clean_text:
                            modified = True
                            leading_ws = text[:len(text) - len(text.lstrip())]
                            trailing_ws = text[len(text.rstrip()):]
                            return f"{prefix}{leading_ws}{html.escape(target)}{trailing_ws}{suffix}"
                return match.group(0)

            # Match text nodes between HTML closing and opening tags >text<
            pattern_text_node = r'(>)([^<>{}%]+)(<)'
            content = re.sub(pattern_text_node, replace_text_node, content)

        # 7. Restore all protected blocks and spans in reverse order
        for idx in range(len(protected) - 1, -1, -1):
            placeholder = f'__TRANS_PROTECT_{idx}__'
            content = content.replace(placeholder, protected[idx])

        if modified:
            response.content = content.encode('utf-8')

        return response
