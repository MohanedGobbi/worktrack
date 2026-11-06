import os
import sys
import json
import re
import time
import urllib.request
import urllib.parse
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from core.models import TranslationItem
from django.db.models import Q

def translate_api(text, target_lang='ar', source_lang='auto'):
    if not text or not text.strip():
        return ""
    clean_text = text.strip()
    # Cache / quick rules
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={urllib.parse.quote(clean_text)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                translated = ''.join([part[0] for part in data[0] if part[0]])
                return translated.strip()
        except Exception as e:
            time.sleep(0.3 * (attempt + 1))
    return None

def main():
    print("=== STARTING COMPREHENSIVE TRANSLATIONS POPULATION ===")
    
    # 1. Load dictionary from i18n.js if available
    ar_dict = {}
    try:
        with open('/tmp/i18n_dict.json', 'r', encoding='utf-8') as f:
            js_data = json.load(f)
            ar_dict = {k.strip().lower(): v.strip() for k, v in js_data.get('ar', {}).items() if v and isinstance(v, str)}
    except Exception as e:
        print("Note: /tmp/i18n_dict.json not loaded:", e)

    # 2. Load existing DB translations
    db_en_to_ar = {}
    db_ar_to_en = {}
    for item in TranslationItem.objects.exclude(english_text__isnull=True).exclude(english_text__exact='').exclude(arabic_text__isnull=True).exclude(arabic_text__exact=''):
        en = item.english_text.strip()
        ar = item.arabic_text.strip()
        if en and ar:
            db_en_to_ar[en.lower()] = ar
            db_ar_to_en[ar.lower()] = en

    # 3. Process missing English entries
    missing_en_items = list(TranslationItem.objects.filter(Q(english_text__isnull=True) | Q(english_text__exact='')))
    print(f"Found {len(missing_en_items)} items missing English text.")

    updated_en_count = 0
    for item in missing_en_items:
        ar_text = (item.arabic_text or '').strip()
        if not ar_text:
            continue
        
        en_text = None
        
        # Check if already in DB reverse map
        if ar_text.lower() in db_ar_to_en:
            en_text = db_ar_to_en[ar_text.lower()]
        
        # Pattern: 'English / Arabic' or 'Arabic / English'
        if not en_text and ' / ' in ar_text:
            parts = [p.strip() for p in ar_text.split(' / ')]
            if len(parts) >= 2:
                if re.search(r'[a-zA-Z]', parts[0]) and not re.search(r'[\u0600-\u06FF]', parts[0]):
                    en_text = parts[0]
                elif re.search(r'[a-zA-Z]', parts[1]) and not re.search(r'[\u0600-\u06FF]', parts[1]):
                    en_text = parts[1]

        # Pattern: 'Arabic (English)' or 'English (Arabic)'
        if not en_text and '(' in ar_text and ')' in ar_text:
            m = re.search(r'\(([^)]+)\)', ar_text)
            if m and re.search(r'[a-zA-Z]', m.group(1)) and not re.search(r'[\u0600-\u06FF]', m.group(1)):
                en_text = m.group(1).strip()
            m2 = re.search(r'^([^(]+)\s*\(([^)]+)\)', ar_text)
            if m2 and re.search(r'[a-zA-Z]', m2.group(1)) and not re.search(r'[\u0600-\u06FF]', m2.group(1)):
                en_text = m2.group(1).strip()

        # If still not found, translate via API
        if not en_text:
            en_text = translate_api(ar_text, target_lang='en', source_lang='ar')

        if en_text:
            item.english_text = en_text
            item.save(update_fields=['english_text'])
            updated_en_count += 1
            if updated_en_count % 20 == 0:
                print(f"  [EN] Updated {updated_en_count}/{len(missing_en_items)}...")

    print(f"--> Successfully populated {updated_en_count} English translations.")

    # 4. Process missing Arabic entries
    missing_ar_items = list(TranslationItem.objects.filter(Q(arabic_text__isnull=True) | Q(arabic_text__exact='')))
    print(f"Found {len(missing_ar_items)} items missing Arabic text.")

    updated_ar_count = 0
    for item in missing_ar_items:
        en_text = (item.english_text or '').strip()
        if not en_text:
            continue

        ar_text = None

        # Check existing dictionaries
        en_lower = en_text.lower()
        if en_lower in db_en_to_ar:
            ar_text = db_en_to_ar[en_lower]
        elif en_lower in ar_dict:
            ar_text = ar_dict[en_lower]

        # Check punctuation cleaned
        if not ar_text:
            en_clean = re.sub(r'[^\w\s]', '', en_lower).strip()
            if en_clean in db_en_to_ar:
                ar_text = db_en_to_ar[en_clean]
            elif en_clean in ar_dict:
                ar_text = ar_dict[en_clean]

        # If not found, translate via API
        if not ar_text:
            ar_text = translate_api(en_text, target_lang='ar', source_lang='en')

        if ar_text:
            item.arabic_text = ar_text
            item.save(update_fields=['arabic_text'])
            updated_ar_count += 1
            if updated_ar_count % 50 == 0:
                print(f"  [AR] Updated {updated_ar_count}/{len(missing_ar_items)}...")

    print(f"--> Successfully populated {updated_ar_count} Arabic translations.")

    # 5. Handle empty text items
    empty_items = TranslationItem.objects.filter(key='auto.global.لوحة_العمليات_التشغيلية')
    for item in empty_items:
        item.english_text = "Operations Dashboard"
        item.arabic_text = "لوحة العمليات التشغيلية"
        item.save(update_fields=['english_text', 'arabic_text'])

    # 6. Final check
    rem_ar = TranslationItem.objects.filter(Q(arabic_text__isnull=True) | Q(arabic_text__exact='')).count()
    rem_en = TranslationItem.objects.filter(Q(english_text__isnull=True) | Q(english_text__exact='')).count()
    total = TranslationItem.objects.count()
    total_translated = TranslationItem.objects.exclude(Q(arabic_text__isnull=True) | Q(arabic_text__exact='') | Q(english_text__isnull=True) | Q(english_text__exact='')).count()

    print("\n=== FINAL TRANSLATION STATUS ===")
    print(f"Total Translation Items: {total}")
    print(f"Fully Translated Items: {total_translated}")
    print(f"Remaining Missing Arabic: {rem_ar}")
    print(f"Remaining Missing English: {rem_en}")

if __name__ == '__main__':
    main()
