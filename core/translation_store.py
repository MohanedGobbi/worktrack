import os
import time
import re
import html
import logging
from django.core.cache import cache
from core.models import TranslationItem

logger = logging.getLogger(__name__)

TS_FILE = '/tmp/translation_last_updated.txt'

_UNIFIED_CACHE = {
    'by_key': {},
    'by_en_norm': {},
    'map_json': {'ar': {}, 'en': {}},
    'version': -1,
    'loaded_at': 0,
}


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
    slug_clean = re.sub(r'^auto\.[^.]+\.', '', k)
    slug_clean = re.sub(r'^auto\.global\.', '', slug_clean)
    if slug_clean and slug_clean not in keys:
        keys.append(slug_clean)
        readable_clean = slug_clean.replace('_', ' ')
        if readable_clean and readable_clean not in keys:
            keys.append(readable_clean)
    return keys


def get_system_translation_version():
    try:
        if os.path.exists(TS_FILE):
            with open(TS_FILE, 'r', encoding='utf-8') as f:
                val = f.read().strip()
                if val:
                    return float(val)
    except Exception:
        pass
    try:
        ver = cache.get('translation_cache_version', 0)
        if ver:
            return float(ver)
    except Exception:
        pass
    return 0


def invalidate_unified_translation_store():
    """Single unified function to instantly invalidate all translation caches across system."""
    global _UNIFIED_CACHE
    _UNIFIED_CACHE['by_key'] = {}
    _UNIFIED_CACHE['by_en_norm'] = {}
    _UNIFIED_CACHE['map_json'] = {'ar': {}, 'en': {}}
    _UNIFIED_CACHE['version'] = -1
    _UNIFIED_CACHE['loaded_at'] = 0

    new_version = time.time()
    try:
        with open(TS_FILE, 'w', encoding='utf-8') as f:
            f.write(str(new_version))
    except Exception:
        pass
    try:
        cache.clear()
        cache.set('translation_cache_version', new_version, timeout=None)
    except Exception:
        pass


def get_unified_translation_store():
    """
    Returns the single unified translation dictionary.
    All components (middleware, template tags, API views) use THIS SINGLE FUNCTION.
    """
    global _UNIFIED_CACHE
    now = time.time()
    current_ver = get_system_translation_version()

    needs_reload = (
        not _UNIFIED_CACHE['by_en_norm']
        or current_ver != _UNIFIED_CACHE['version']
        or (now - _UNIFIED_CACHE['loaded_at']) > 0.5
    )

    if needs_reload:
        try:
            items = list(TranslationItem.objects.order_by('-updated_at', '-id'))
            by_key = {}
            by_en_norm = {}
            api_map = {'ar': {}, 'en': {}}

            for item in items:
                en_text = (item.english_text or '').strip()
                ar_text = (item.arabic_text or '').strip()
                key_text = (item.key or '').strip()
                ctx_text = (item.context or '').strip()

                val = {
                    'en': en_text,
                    'ar': ar_text,
                    'key': key_text
                }

                lookup_keys = set()
                if key_text:
                    for k in _extract_slug_from_key(key_text):
                        lookup_keys.add(k)
                        if k not in by_key:
                            by_key[k] = val
                if en_text:
                    for k in _normalize_key_or_text(en_text):
                        lookup_keys.add(k)
                if ar_text:
                    for k in _normalize_key_or_text(ar_text):
                        lookup_keys.add(k)
                if ctx_text and 'Original:' in ctx_text:
                    orig = ctx_text.split('Original:')[1].strip()
                    for k in _normalize_key_or_text(orig):
                        lookup_keys.add(k)

                for k in lookup_keys:
                    if k and k not in by_en_norm:
                        by_en_norm[k] = val
                    if k and k not in by_key:
                        by_key[k] = val

                if ar_text and any('\u0600' <= ch <= '\u06FF' for ch in ar_text):
                    for k in lookup_keys:
                        api_map['ar'][k] = ar_text
                if en_text:
                    for k in lookup_keys:
                        api_map['en'][k] = en_text

            _UNIFIED_CACHE['by_key'] = by_key
            _UNIFIED_CACHE['by_en_norm'] = by_en_norm
            _UNIFIED_CACHE['map_json'] = api_map
            _UNIFIED_CACHE['version'] = current_ver
            _UNIFIED_CACHE['loaded_at'] = now
        except Exception as e:
            logger.error(f"Error loading unified translation store: {e}")

    return _UNIFIED_CACHE


def lookup_unified_translation(raw_text):
    if not raw_text:
        return None
    clean = html.unescape(re.sub(r'<[^>]+>', '', str(raw_text))).strip()
    if not clean:
        return None
    
    store = get_unified_translation_store()
    by_en_norm = store['by_en_norm']
    by_key = store['by_key']

    clean_lower = clean.lower()
    slug = re.sub(r'[^\w]+', '_', clean_lower).strip('_')
    readable = slug.replace('_', ' ')

    candidates = [clean, clean_lower, slug, readable]

    for cand in candidates:
        if cand:
            if cand in by_key:
                return by_key[cand]
            if cand in by_en_norm:
                return by_en_norm[cand]

    return None
