import os
import time
import logging
from django import template
from django.core.cache import cache
from core.models import TranslationItem

logger = logging.getLogger(__name__)
register = template.Library()

_LOCAL_CACHE = {
    'by_key': {},
    'by_en': {},
    'mtime': 0,
}

TS_FILE = '/tmp/translation_last_updated.txt'
CACHE_VERSION_KEY = 'translation_cache_version'

def _get_ts_file_mtime():
    try:
        if os.path.exists(TS_FILE):
            return os.path.getmtime(TS_FILE)
    except Exception:
        pass
    return 0


def _get_cache_version():
    try:
        version = cache.get(CACHE_VERSION_KEY, 0)
        return version or 0
    except Exception:
        return 0


def _current_translation_version():
    version = _get_cache_version()
    if version:
        return version
    return _get_ts_file_mtime()


def _touch_translation_version():
    new_version = time.time()
    try:
        cache.set(CACHE_VERSION_KEY, new_version, timeout=None)
    except Exception:
        pass
    try:
        with open(TS_FILE, 'w', encoding='utf-8') as f:
            f.write(str(new_version))
    except Exception:
        pass


import re

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

def load_translation_maps():
    store = get_unified_translation_store()
    global _LOCAL_CACHE
    _LOCAL_CACHE['by_key'] = store['by_key']
    _LOCAL_CACHE['by_en'] = store['by_en_norm']
    _LOCAL_CACHE['mtime'] = store['version']

@register.simple_tag(takes_context=True)
def trans_db(context, key_or_text, default='', ctx_str=''):
    """
    Template tag for database-backed translations.
    Looks up by key FIRST, then by English text fallback.
    Usage: {% trans_db 'dashboard.title' default='Dashboard' %}
           {% trans_db 'Dashboard' %}
    """
    request = context.get('request')
    lang = 'en'
    if request:
        lang = request.COOKIES.get('django_language') or request.COOKIES.get('worktrack_lang') or 'en'
    
    load_translation_maps()
    by_key = _LOCAL_CACHE['by_key']
    by_en = _LOCAL_CACHE['by_en']
    
    lookup_str = key_or_text or default
    if not lookup_str:
        return ''
    
    entry = None
    # 1. Try exact key match
    if lookup_str in by_key:
        entry = by_key[lookup_str]
    # 2. Try English text match
    else:
        norm_str = lookup_str.strip().lower()
        if norm_str in by_en:
            entry = by_en[norm_str]
        elif default:
            norm_def = default.strip().lower()
            if norm_def in by_en:
                entry = by_en[norm_def]
                
    if entry:
        val = entry.get(lang)
        if val:
            return val
        fallback = entry.get('en')
        return fallback if fallback else (default or key_or_text)
    
    # 3. Dynamic auto-registration if missing completely
    try:
        TranslationItem.objects.get_or_create(
            key=lookup_str,
            defaults={
                'english_text': default or lookup_str,
                'context': ctx_str or 'auto-registered'
            }
        )
        _touch_translation_version()
    except Exception as e:
        logger.error(f"Error auto-registering key {lookup_str}: {e}")
        
    return default or key_or_text

@register.simple_tag(takes_context=True, name='t')
def trans_tag(context, key_or_text, default='', ctx_str=''):
    """Alias tag {% t 'string' %} for trans_db."""
    return trans_db(context, key_or_text, default=default, ctx_str=ctx_str)


@register.filter(name='t')
def trans_filter(text, lang='ar'):
    """
    Filter for translating strings in templates:
    {{ "Dashboard"|t }}
    """
    if not text:
        return ''
    load_translation_maps()
    by_en = _LOCAL_CACHE['by_en']
    norm = str(text).strip().lower()
    if norm in by_en:
        entry = by_en[norm]
        return entry.get(lang) or entry.get('ar') or entry.get('en') or text
    return text
