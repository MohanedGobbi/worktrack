#!/usr/bin/env python3
import os
import re
import sqlite3

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(ROOT, 'db.sqlite3')

BILINGUAL_RE = re.compile(r'<span[^>]*class=["\']lang-en["\'][^>]*>(.*?)</span>\s*<span[^>]*class=["\']lang-ar["\'][^>]*>(.*?)</span>', re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r'<[^>]+>')
TEXT_NODE_RE = re.compile(r'>([^<>{}%]+)<')
ATTR_TEXT_RE = re.compile(r'\b(?:placeholder|title|alt|aria-label|value|data-i18n-title-en|data-i18n-title-ar)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)


def strip_tags(s):
    return TAG_RE.sub('', s or '').strip()


def has_arabic(s):
    return any('\u0600' <= c <= '\u06FF' for c in (s or ''))


def scan_templates_for_bilingual(root_dir):
    en_to_ar = {}
    ar_to_en = {}
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            if not fn.lower().endswith('.html'):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    c = f.read()
            except Exception:
                continue
            for m in BILINGUAL_RE.finditer(c):
                en = strip_tags(m.group(1))
                ar = strip_tags(m.group(2))
                if en and ar:
                    en_to_ar[en.lower()] = ar
                    ar_to_en[ar] = en
    return en_to_ar, ar_to_en


def make_readable_from_key(key):
    # remove auto prefixes
    slug = re.sub(r'^auto\.global\.', '', key or '')
    slug = re.sub(r'^auto\.[^.]+\.', '', slug)
    slug = slug.replace('.', '_')
    slug = re.sub(r'[^\w]+', ' ', slug).strip()
    if not slug:
        return None
    return slug.title()


def main():
    if not os.path.exists(DB_PATH):
        print('DB not found at', DB_PATH)
        return

    print('Scanning templates for bilingual spans...')
    en_to_ar, ar_to_en = scan_templates_for_bilingual(ROOT)
    print('bilingual pairs (en->ar):', len(en_to_ar))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch rows missing english_text
    cur.execute("SELECT id, key, english_text, arabic_text FROM core_translationitem WHERE english_text IS NULL OR trim(english_text) = ''")
    rows = cur.fetchall()
    print('rows missing english:', len(rows))

    filled = 0
    for row in rows:
        rid = row['id']
        key = row['key'] or ''
        ar = (row['arabic_text'] or '').strip()
        new_eng = None
        # 1) If arabic exists and mapping found
        if ar and ar in ar_to_en:
            new_eng = ar_to_en[ar]
        # 2) If key is auto.* create readable
        if not new_eng:
            readable = make_readable_from_key(key)
            if readable and not has_arabic(readable):
                new_eng = readable
        # 3) As fallback, try to find english by searching en_to_ar keys for exact ar mapping
        if not new_eng and ar:
            for e, a in en_to_ar.items():
                if a == ar:
                    new_eng = e
                    break
        if new_eng:
            cur.execute("UPDATE core_translationitem SET english_text = ? WHERE id = ?", (new_eng, rid))
            filled += 1
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM core_translationitem WHERE english_text IS NULL OR trim(english_text) = ''")
    remaining = cur.fetchone()[0]

    print('Filled english for:', filled)
    print('Remaining missing english:', remaining)

    conn.close()

if __name__ == '__main__':
    main()
