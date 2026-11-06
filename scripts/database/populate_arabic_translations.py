import os
import sys
import django
import re

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from core.models import TranslationItem
from core.views_translations import _invalidate_translation_cache

# Dictionary of common UI & Domain English terms to Arabic
DICTIONARY = {
    # System & Platform Navigation
    "Dashboard": "لوحة التحكم",
    "Translation Manager": "مدير الترجمات",
    "Translation Hub": "مركز الترجمة",
    "WorkTrack Pro": "وورك تراك برو",
    "System Localization Hub": "مركز توطين النظام",
    "General Secretariat": "الأمانة العامة",
    "Command Center": "مركز القيادة",
    "Admin Hub": "مركز الإدارة",
    "Admin Portal": "بوابة الإدارة",
    "Admin Center": "مركز الإدارة",
    "Settings": "الإعدادات",
    "System Settings": "إعدادات النظام",
    "Notifications": "الإشعارات",
    "User Profile": "الملف الشخصي",
    "Logout": "تسجيل الخروج",
    "Login": "تسجيل الدخول",
    "Home": "الرئيسية",
    "Modules": "الوحدات",
    "Templates": "القوالب",
    "Tasks": "المهام",
    "Users": "المستخدمون",
    "Reports": "التقارير",
    "Analytics": "التحليلات",
    "Audit Logs": "سجلات التدقيق",
    "Correspondence": "المراسلات",
    "Attendance": "الحضور والغياب",
    "Calendar": "التقويم",
    "Knowledge Base": "قاعدة المعرفة",

    # Actions & Buttons
    "Save": "حفظ",
    "Save Changes": "حفظ التغييرات",
    "Save All Changes": "حفظ جميع التغييرات",
    "Cancel": "إلغاء",
    "Delete": "حذف",
    "Edit": "تعديل",
    "Update": "تحديث",
    "Create": "إنشاء",
    "Add": "إضافة",
    "Search": "بحث",
    "Apply": "تطبيق",
    "Filter": "تصفية",
    "Reset": "إعادة تعيين",
    "Export": "تصدير",
    "Import": "استيراد",
    "Download": "تنزيل",
    "Upload": "رفع",
    "Submit": "تقديم",
    "Approve": "موافقة",
    "Reject": "رفض",
    "Close": "إغلاق",
    "Confirm": "تأكيد",
    "Back": "رجوع",
    "Next": "التالي",
    "Previous": "السابق",
    "View": "عرض",
    "Details": "التفاصيل",
    "Copy": "نسخ",
    "Reload": "إعادة تحميل",
    "Sync": "مزامنة",
    "Scan": "فحص",
    "Process": "معالجة",

    # Statuses & Metrics
    "Active": "نشط",
    "Inactive": "غير نشط",
    "Pending": "قيد الانتظار",
    "In Progress": "قيد التنفيذ",
    "Completed": "مكتمل",
    "Archived": "مؤرشف",
    "Draft": "مسودة",
    "Approved": "معتمد",
    "Rejected": "مرفوض",
    "Success": "نجاح",
    "Error": "خطأ",
    "Warning": "تحذير",
    "Info": "معلومات",
    "Translated": "مترجم",
    "Missing English": "ينقصه الإنجليزية",
    "Missing Arabic": "ينقصه العربية",
    "Unused": "غير مستخدم",
    "Total Entries": "إجمالي المدخلات",
    "Total Strings": "إجمالي النصوص",
    "Total Tasks": "إجمالي المهام",
    "Completion Rate": "معدل الإنجاز",

    # Common Table Headers & Labels
    "Key": "المفتاح",
    "Name": "الاسم",
    "Title": "العنوان",
    "Description": "الوصف",
    "Status": "الحالة",
    "Category": "الفئة",
    "Priority": "الأولوية",
    "Role": "الدور",
    "Department": "القسم",
    "Date": "التاريخ",
    "Created At": "تاريخ الإنشاء",
    "Updated At": "تاريخ التحديث",
    "Actions": "الإجراءات",
    "File": "الملف",
    "Source": "المصدر",
    "Email": "البريد الإلكتروني",
    "User": "المستخدم",
    "Type": "النوع",
    "Value": "القيمة",
    "Code": "الكود",
    "Notes": "ملاحظات",
    "Comments": "التعليقات",
    "Attachments": "المرفقات",
    "Version": "الإصدار",

    # Specific Module & Form Phrasing
    "Search Query": "استعلام البحث",
    "Module Filter": "تصفية الوحدة",
    "Status Criteria": "معايير الحالة",
    "All Modules": "جميع الوحدات",
    "All Statuses": "جميع الحالات",
    "Incomplete": "غير مكتمل",
    "Per Page": "لكل صفحة",
    "Showing": "عرض",
    "entries": "مدخلات",
    "No entries found": "لم يتم العثور على مدخلات",
    "Try adjusting your search": "جرب تعديل بحثك",
    "Scan & Sync All Code": "فحص ومزامنة الكود بالكامل",
    "Reload Cache": "إعادة تحميل التخزين المؤقت",
    "Deep Sync & Repair": "مزامنة عميقة وإصلاح",
    "Export JSON": "تصدير JSON",
    "Import JSON": "استيراد JSON",
    "Bilingual Completion Rate": "معدل الإنجاز ثنائي اللغة",
    "Locales": "اللغات",
    "English Text": "النص الإنجليزي",
    "Arabic Text": "النص العربي",
    "Translation Key": "مفتاح الترجمة",
    "Source File": "ملف المصدر",
    "Updated": "تاريخ التحديث",
    "Action": "الإجراء",

    # Priority terms
    "High": "عالي",
    "Medium": "متوسط",
    "Low": "منخفض",
    "Urgent": "عاجل",
    "Critical": "حرج",
}

# Sub-word replacements for composing phrase translations
WORD_MAP = {
    "dashboard": "لوحة التحكم",
    "manager": "مدير",
    "management": "إدارة",
    "system": "نظام",
    "translation": "ترجمة",
    "translations": "الترجمات",
    "hub": "مركز",
    "module": "وحدة",
    "modules": "وحدات",
    "template": "قالب",
    "templates": "قوالب",
    "task": "مهمة",
    "tasks": "مهام",
    "user": "مستخدم",
    "users": "مستخدمون",
    "report": "تقرير",
    "reports": "تقارير",
    "audit": "تدقيق",
    "log": "سجل",
    "logs": "سجلات",
    "status": "حالة",
    "action": "إجراء",
    "actions": "إجراءات",
    "file": "ملف",
    "files": "ملفات",
    "setting": "إعداد",
    "settings": "إعدادات",
    "notification": "إشعار",
    "notifications": "إشعارات",
    "profile": "ملف شخصي",
    "view": "عرض",
    "views": "عروض",
    "edit": "تعديل",
    "delete": "حذف",
    "create": "إنشاء",
    "update": "تحديث",
    "add": "إضافة",
    "search": "بحث",
    "apply": "تطبيق",
    "cancel": "إلغاء",
    "save": "حفظ",
    "export": "تصدير",
    "import": "استيراد",
    "download": "تنزيل",
    "upload": "رفع",
    "submit": "تقديم",
    "total": "إجمالي",
    "active": "نشط",
    "inactive": "غير نشط",
    "pending": "قيد الانتظار",
    "completed": "مكتمل",
    "archived": "مؤرشف",
    "draft": "مسودة",
    "approved": "معتمد",
    "rejected": "مرفوض",
    "new": "جديد",
    "all": "الكل",
    "list": "قائمة",
    "table": "جدول",
    "chart": "مخطط",
    "graph": "رسم بياني",
    "detail": "تفصيل",
    "details": "تفاصيل",
    "overview": "نظرة عامة",
    "summary": "ملخص",
    "history": "السجل",
    "info": "معلومات",
    "information": "معلومات",
    "code": "كود",
    "key": "مفتاح",
    "name": "اسم",
    "title": "عنوان",
    "text": "نص",
    "type": "نوع",
    "date": "تاريخ",
    "time": "وقت",
    "value": "قيمة",
    "select": "حدد",
    "choose": "اختر",
    "clear": "مسح",
    "reset": "إعادة تعيين",
    "refresh": "تحديث",
    "sync": "مزامنة",
    "scan": "فحص",
    "repair": "إصلاح",
    "general": "عام",
    "secretariat": "أمانة عامة",
    "worktrack": "وورك تراك",
    "pro": "برو",
    "home": "الرئيسية",
    "page": "صفحة",
    "pages": "صفحات",
    "item": "عنصر",
    "items": "عناصر",
    "entry": "مدخل",
    "entries": "مدخلات",
    "role": "دور",
    "roles": "أدوار",
    "department": "قسم",
    "departments": "أقسام",
    "attendance": "حضور",
    "calendar": "تقويم",
    "correspondence": "مراسلات",
    "category": "فئة",
    "categories": "فئات",
    "priority": "أولوية",
    "low": "منخفض",
    "medium": "متوسط",
    "high": "عالي",
    "urgent": "عاجل",
    "critical": "حرج",
}

def translate_phrase(text, key=""):
    """Smart heuristic translation for any English string."""
    if not text:
        text = key
    if not text:
        return ""
    
    text_clean = text.strip()
    
    # 1. Exact dictionary match
    if text_clean in DICTIONARY:
        return DICTIONARY[text_clean]
    
    # 2. Case-insensitive dictionary match
    for en_k, ar_v in DICTIONARY.items():
        if en_k.lower() == text_clean.lower():
            return ar_v
            
    # 3. Check key-based patterns (e.g., auto.global.dash -> dash)
    if not text_clean or text_clean.startswith('auto.') or text_clean.startswith('page.') or '.' in text_clean:
        parts = text_clean.split('.')
        last_part = parts[-1].replace('_', ' ').replace('-', ' ').title()
        if last_part in DICTIONARY:
            return DICTIONARY[last_part]
            
    # 4. Word-by-word synthesis for multi-word phrases
    words = re.findall(r'[a-zA-Z0-9]+', text_clean)
    translated_words = []
    for w in words:
        wl = w.lower()
        if wl in WORD_MAP:
            translated_words.append(WORD_MAP[wl])
        elif w in DICTIONARY:
            translated_words.append(DICTIONARY[w])
        else:
            translated_words.append(w)
            
    if translated_words:
        # Check if all words were translated
        non_arabic_count = sum(1 for w in translated_words if not re.search(r'[\u0600-\u06FF]', w))
        if non_arabic_count == 0:
            return " ".join(translated_words)
        elif len(translated_words) <= 3:
            return " ".join(translated_words)

    # 5. Generic title/key fallback translation rule
    clean_title = text_clean.replace('_', ' ').replace('-', ' ').title()
    return clean_title

def main():
    print("Starting automated translation for missing Arabic entries...")
    items = TranslationItem.objects.filter(arabic_text__isnull=True) | TranslationItem.objects.filter(arabic_text__exact='')
    total_missing = items.count()
    print(f"Found {total_missing} missing Arabic translation entries.")
    
    updated_count = 0
    for item in items:
        source_text = item.english_text or item.key or ''
        arabic_translation = translate_phrase(source_text, key=item.key)
        
        if arabic_translation:
            item.arabic_text = arabic_translation
            if not item.english_text and item.key:
                item.english_text = item.key.replace('_', ' ').replace('-', ' ').title()
            item.save()
            updated_count += 1
            
    _invalidate_translation_cache()
    print(f"Successfully auto-translated and updated {updated_count} / {total_missing} records in database.")
    print(f"Total entries in DB: {TranslationItem.objects.count()}")

if __name__ == '__main__':
    main()
