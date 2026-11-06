#!/usr/bin/env python3
import os
import re
import sqlite3

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(ROOT, 'db.sqlite3')

BILINGUAL_RE = re.compile(r'<span[^>]*class=["\']lang-en["\'][^>]*>(.*?)</span>\s*<span[^>]*class=["\']lang-ar["\'][^>]*>(.*?)</span>', re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r'<[^>]+>')
ARABIC_RANGE = (0x0600, 0x06FF)

def strip_tags(s):
    return TAG_RE.sub('', s or '').strip()

def has_arabic(s):
    return any('\u0600' <= c <= '\u06FF' for c in (s or ''))

def scan_bilingual_spans(root_dir):
    en_to_ar = {}
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
                if en and ar and len(en) >= 2:
                    en_to_ar[en.lower()] = ar
    return en_to_ar


def main():
    if not os.path.exists(DB_PATH):
        print('DB not found at', DB_PATH)
        return

    print('Scanning templates for bilingual spans...')
    en_to_ar = scan_bilingual_spans(ROOT)
    print('Bilingual pairs found:', len(en_to_ar))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    updated_ar = 0
    updated_en = 0

    cur.execute("SELECT id, key, english_text, arabic_text FROM core_translationitem")
    rows = cur.fetchall()
    for row in rows:
        rid = row['id']
        key = row['key'] or ''
        eng = (row['english_text'] or '').strip()
        ar = (row['arabic_text'] or '').strip()
        changed = False
        # Fill Arabic via bilingual mapping
        if eng and not ar:
            ar_match = en_to_ar.get(eng.lower())
            if ar_match:
                cur.execute("UPDATE core_translationitem SET arabic_text = ? WHERE id = ?", (ar_match, rid))
                updated_ar += 1
                changed = True
        # Fill English from auto key
        if not eng:
            slug = re.sub(r'^auto\.global\.', '', key or '')
            slug = re.sub(r'^auto\.[^.]+\.', '', slug)
            readable = slug.replace('_', ' ').strip()
            if readable and len(readable) >= 2 and not has_arabic(readable):
                eng_val = readable.title()
                cur.execute("UPDATE core_translationitem SET english_text = ? WHERE id = ?", (eng_val, rid))
                updated_en += 1
                changed = True
    conn.commit()

    # Deduplicate by english_text
    merged_groups = 0
    merged_rows = 0
    cur.execute("SELECT english_text, COUNT(*) as cnt FROM core_translationitem WHERE english_text IS NOT NULL AND trim(english_text) != '' GROUP BY english_text HAVING cnt > 1")
    dups = cur.fetchall()
    for d in dups:
        en = d['english_text']
        cur.execute("SELECT id, arabic_text, updated_at FROM core_translationitem WHERE english_text = ? ORDER BY updated_at DESC, id DESC", (en,))
        items = cur.fetchall()
        if len(items) < 2:
            continue
        keep = items[0]
        others = items[1:]
        keep_id = keep['id']
        keep_ar = (keep['arabic_text'] or '').strip()
        changed = False
        for o in others:
            oid = o['id']
            o_ar = (o['arabic_text'] or '').strip()
            if (not keep_ar) and o_ar:
                cur.execute("UPDATE core_translationitem SET arabic_text = ? WHERE id = ?", (o_ar, keep_id))
                keep_ar = o_ar
                changed = True
            cur.execute("DELETE FROM core_translationitem WHERE id = ?", (oid,))
            merged_rows += 1
        if changed:
            pass
        merged_groups += 1
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM core_translationitem WHERE english_text IS NOT NULL AND trim(english_text) != '' AND arabic_text IS NOT NULL AND trim(arabic_text) != ''")
    total_both = cur.fetchone()[0]

    print('Deep sync complete.')
    print('English recovered:', updated_en)
    print('Arabic matched:', updated_ar)
    print('Dedup groups:', merged_groups)
    print('Rows removed during dedupe:', merged_rows)
    print('Total with both:', total_both)

    conn.close()

if __name__ == '__main__':
    main()
