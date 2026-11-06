import os
import sys
import re
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from core.models import TranslationItem
from core.views_translations import _invalidate_translation_cache

# Direct phrase mapping from english_text (or cleaned key) to clean, professional Arabic
PHRASE_TRANSLATIONS = {
    "page not found": "الصفحة غير موجودة",
    "go to dashboard": "الذهاب إلى لوحة التحكم",
    "go back": "الرجوع للخلف",
    "admin dashboard": "لوحة تحكم المسؤول",
    "admin dashboard ui": "واجهة لوحة تحكم المسؤول",
    "admin delete": "حذف بواسطة المسؤول",
    "admin edit": "تعديل بواسطة المسؤول",
    "admin hub": "مركز الإدارة",
    "admin portal": "بوابة الإدارة",
    "admin center": "مركز الإدارة",
    "system admin": "مسؤول النظام",
    "admin_panel_settings": "إعدادات لوحة التحكم",
    "administration / correspondence": "الإدارة والمراسلات",
    "administrative category": "الفئة الإدارية",
    "academic email": "البريد الإلكتروني الأكاديمي",
    "accept all ips": "قبول جميع عناوين IP",
    "accepting all ips": "قبول كافة عناوين IP",
    "access ip": "عنوان IP للوصول",
    "access point (ip)": "نقطة الوصول (IP)",
    "account status": "حالة الحساب",
    "active board": "اللوحة النشطة",
    "active days": "الأيام النشطة",
    "active deadline": "الموعد النهائي النشط",
    "active deployment": "النشر التشغيلي النشط",
    "active depts": "الأقسام النشطة",
    "active nodes": "العقد النشطة",
    "active now": "نشط الآن",
    "active only": "النشط فقط",
    "active ops": "العمليات النشطة",
    "active pending": "نشط وقيد الإنجاز",
    "active personnel": "الموظفون النشطون",
    "active polls": "استطلاعات الرأي النشطة",
    "active right now": "نشط الآن",
    "active team members": "أعضاء الفريق النشطون",
    "add project": "إضافة مشروع",
    "add_research_metric": "إضافة مقياس بحثي",
    "add_service": "إضافة خدمة",
    "add strategic note": "إضافة ملاحظة استراتيجية",
    "add todo": "إضافة مهمة جديدة",
    "add workflow unit": "إضافة وحدة عمل",
    "additional attachments": "مرفقات إضافية",
    "all caught up!": "تم إنجاز كافة المهام!",
    "all contexts": "كافة الوحدات",
    "all modes": "كافة الأوضاع",
    "all priorities": "كافة الأولويات",
    "all ranks": "كافة الرتب",
    "all records": "كافة السجلات",
    "all status": "كافة الحالات",
    "all submissions": "كافة التسليمات",
    "all types": "كافة الأنواع",
    "allow all contacts": "السماح لجميع جهات الاتصال",
    "app name & colors": "اسم التطبيق والألوان",
    "apply filters": "تطبيق عوامل التصفية",
    "approve selected": "الموافقة على المحدد",
    "approve submission": "الموافقة على التسليم",
    "arabic text (rtl)": "النص العربي (من اليمين لليسار)",
    "archived / done": "مؤرشف / مكتمل",
    "archived units": "الوحدات المؤرشفة",
    "arrow_back": "رجوع للخلف",
    "arrow_forward": "تقدم للأمام",
    "associated files & media": "الملفات والوسائط المرتبطة",
    "associated task": "المهمة المرتبطة",
    "attach_file": "إرفاق ملف",
    "attached files": "الملفات المرفقة",
    "attendance configuration": "إعدادات الحضور والغياب",
    "attendance policy settings": "إعدادات سياسة الحضور",
    "attendance tracking": "تتبع الحضور والغياب",
    "attendance tracking (new)": "تتبع الحضور والغياب (جديد)",
    "average module progress": "متوسط تقدم الوحدة",
    "avg. module progress": "متوسط تقدم الوحدة",
    "avg task": "متوسط إنجاز المهام",
    "back to dashboard": "الرجوع إلى لوحة التحكم",
    "back to hub": "الرجوع إلى المركز",
    "back to login": "الرجوع إلى تسجيل الدخول",
    "back to task": "الرجوع إلى المهمة",
    "back to templates": "الرجوع إلى القوالب",
    "badge text (english)": "نص الشارة",
    "banner text color": "لون نص اللافتة",
    "batch sync & caching": "المزامنة الجماعية والتخزين المؤقت",
    "batch task sync": "مزامنة المهام الجماعية",
    "bio & academic profile": "السيرة الذاتية والملف الأكاديمي",
    "biography info": "معلومات السيرة الذاتية",
    "biography / notes": "السيرة الذاتية والملاحظات",
    "biography summary (english)": "ملخص السيرة الذاتية",
    "border focus (rgba)": "تركيز الحدود",
    "bulk delete": "حذف جماعي",
    "centralize ui text": "توحيد نصوص الواجهة",
    "change module context": "تغيير سياق الوحدة",
    "chat_bubble": "محادثة",
    "chat_bubble_outline": "رمز المحادثة",
    "check_circle": "مكتمل",
    "check your email": "تحقق من بريدك الإلكتروني",
    "checklist_rtl": "قائمة التحقق",
    "chevron_left": "سهم لليسار",
    "chevron_right": "سهم لليمين",
    "choose a color": "اختر لوناً",
    "choose layout": "اختر التخطيط",
    "clear all cache": "مسح كامل التخزين المؤقت",
    "clear all selections": "إلغاء كافة التحديدات",
    "client name": "اسم العميل",
    "cloud infrastructure & devops": "البنية التحتية السحابية وعمليات التطوير",
    "command home": "الرئيسية للقيادة",
    "command hub": "مركز القيادة والتحكم",
    "comms module": "وحدة الاتصالات",
    "completed": "مكتمل",
    "create group chat": "إنشاء محادثة جماعية",
    "create poll": "إنشاء استطلاع رأي",
    "export tasks csv": "تصدير المهام كملف بيانات",
    "file attached": "ملف مرفق",
    "global search": "البحث الشامل",
    "grid view": "عرض شبكي",
    "group name": "اسم المجموعة",
    "impersonation mode active:": "وضع انتحال الشخصية نشط:",
    "install modules": "تثبيت الوحدات",
    "language اللغة": "اللغة",
    "manager portal": "بوابة المدير",
    "profile &amp; avatar": "الملف الشخصي والصورة الشخصية",
    "report the issue": "الإبلاغ عن المشكلة",
    "search contacts...": "البحث في جهات الاتصال...",
    "search conversations...": "البحث في المحادثات...",
    "search in chat...": "البحث في المحادثة...",
    "select messages": "تحديد الرسائل",
    "server error": "خطأ في الخادم",
    "show per page": "عرض في كل صفحة",
    "team analytics": "تحليلات الفريق",
    "team tasks": "مهام الفريق",
    "total system messages": "إجمالي رسائل النظام",
    "type your message...": "اكتب رسالتك هنا...",
    "view archived chats": "عرض المحادثات المؤرشفة",
    "worktrack pro": "وورك تراك برو",
}

# General word substitution mapping for any remaining Latin words inside Arabic text
WORD_REPLACEMENTS = {
    "worktrack": "وورك تراك",
    "pro": "برو",
    "academic": "الأكاديمي",
    "email": "البريد الإلكتروني",
    "status": "الحالة",
    "account": "الحساب",
    "board": "اللوحة",
    "days": "أيام",
    "deadline": "الموعد النهائي",
    "deployment": "النشر التشغيلي",
    "depts": "الأقسام",
    "nodes": "العقد",
    "now": "الآن",
    "only": "فقط",
    "ops": "العمليات",
    "pending": "قيد الإنجاز",
    "personnel": "الموظفين",
    "polls": "استطلاعات الرأي",
    "poll": "استطلاع رأي",
    "right": "حالياً",
    "team": "الفريق",
    "members": "الأعضاء",
    "member": "عضو",
    "project": "مشروع",
    "projects": "المشاريع",
    "research": "البحث",
    "metric": "مقياس",
    "metrics": "مقاييس",
    "service": "خدمة",
    "services": "الخدمات",
    "strategic": "استراتيجي",
    "note": "ملاحظة",
    "notes": "ملاحظات",
    "todo": "مهمة",
    "todos": "المهام",
    "workflow": "سير العمل",
    "unit": "وحدة",
    "units": "الوحدات",
    "module": "وحدة",
    "modules": "الوحدات",
    "additional": "إضافي",
    "attachments": "المرفقات",
    "attachment": "المرفق",
    "attached": "مرفق",
    "admin": "المسؤول",
    "administration": "الإدارة",
    "administrative": "إداري",
    "ui": "واجهة المستخدم",
    "delete": "حذف",
    "edit": "تعديل",
    "panel": "لوحة",
    "settings": "إعدادات",
    "category": "فئة",
    "all": "كافة",
    "contexts": "السياقات",
    "context": "سياق",
    "modes": "الأوضاع",
    "mode": "وضع",
    "priorities": "الأولويات",
    "priority": "أولوية",
    "ranks": "الرتب",
    "rank": "رتبة",
    "records": "السجلات",
    "record": "سجل",
    "submissions": "التسليمات",
    "submission": "تسليم",
    "types": "الأنواع",
    "type": "نوع",
    "allow": "السماح",
    "app": "تطبيق",
    "name": "الاسم",
    "colors": "الألوان",
    "color": "اللون",
    "apply": "تطبيق",
    "filters": "عوامل التصفية",
    "filter": "تصفية",
    "approve": "موافقة",
    "approved": "معتمد",
    "selected": "المحدد",
    "arabic": "العربية",
    "text": "النص",
    "rtl": "من اليمين لليسار",
    "archived": "مؤرشف",
    "archive": "أرشيف",
    "done": "مكتمل",
    "arrow": "سهم",
    "back": "رجوع",
    "forward": "تقدم",
    "associated": "مرتبط",
    "files": "ملفات",
    "file": "ملف",
    "media": "وسائط",
    "task": "مهمة",
    "tasks": "مهام",
    "configuration": "إعدادات",
    "configurations": "إعدادات",
    "config": "إعداد",
    "policy": "سياسة",
    "policies": "سياسات",
    "tracking": "تتبع",
    "track": "تتبع",
    "average": "متوسط",
    "avg": "متوسط",
    "progress": "التقدم",
    "hub": "مركز",
    "login": "تسجيل الدخول",
    "logout": "تسجيل الخروج",
    "templates": "قوالب",
    "template": "قالب",
    "badge": "شارة",
    "english": "الإنجليزية",
    "banner": "لافتة",
    "batch": "جماعي",
    "sync": "مزامنة",
    "caching": "تخزين مؤقت",
    "cache": "تخزين مؤقت",
    "bio": "السيرة الذاتية",
    "biography": "السيرة الذاتية",
    "info": "معلومات",
    "summary": "ملخص",
    "border": "الحدود",
    "focus": "التركيز",
    "rgba": "الألوان",
    "bulk": "جماعي",
    "centralize": "توحيد",
    "change": "تغيير",
    "chat": "محادثة",
    "chats": "محادثات",
    "bubble": "فقاعة",
    "outline": "مخطط",
    "check": "تحقق",
    "circle": "دائرة",
    "your": "الخاص بك",
    "checklist": "قائمة التحقق",
    "chevron": "سهم",
    "choose": "اختر",
    "layout": "تخطيط",
    "clear": "مسح",
    "selections": "التحديدات",
    "client": "العميل",
    "cloud": "السحابة",
    "infrastructure": "البنية التحتية",
    "devops": "عمليات التطوير",
    "home": "الرئيسية",
    "command": "القيادة",
    "comms": "الاتصالات",
    "create": "إنشاء",
    "export": "تصدير",
    "import": "استيراد",
    "global": "شامل",
    "search": "بحث",
    "grid": "شبكة",
    "view": "عرض",
    "group": "مجموعة",
    "groups": "مجموعات",
    "impersonation": "انتحال الشخصية",
    "install": "تثبيت",
    "language": "اللغة",
    "portal": "بوابة",
    "profile": "الملف الشخصي",
    "avatar": "الصورة الرمزية",
    "amp": "و",
    "report": "تقرير",
    "issue": "المشكلة",
    "contacts": "جهات الاتصال",
    "contact": "جهة اتصال",
    "conversations": "المحادثات",
    "conversation": "محادثة",
    "in": "في",
    "select": "تحديد",
    "messages": "الرسائل",
    "message": "رسالة",
    "server": "الخادم",
    "error": "خطأ",
    "show": "عرض",
    "per": "لكل",
    "page": "صفحة",
    "analytics": "تحليلات",
    "total": "إجمالي",
    "system": "النظام",
    "data": "بيانات",
    "open": "فتح",
    "landing": "الهبوط",
    "recent": "الأخيرة",
    "security": "الأمان",
    "icon": "أيقونة",
    "operational": "تشغيلي",
    "real": "حقيقي",
    "time": "الوقت",
    "sort": "ترتيب",
    "last": "الأخير",
    "first": "الأول",
    "location": "الموقع",
    "manage": "إدارة",
    "rate": "معدل",
    "request": "طلب",
    "country": "البلد",
    "alerts": "تنبيهات",
    "alert": "تنبيه",
    "general": "عام",
    "hero": "البانر",
    "optional": "اختياري",
    "password": "كلمة المرور",
    "current": "الحالي",
    "new": "جديد",
    "help": "مساعدة",
    "support": "دعم",
    "user": "مستخدم",
    "users": "مستخدمين",
    "role": "دور",
    "roles": "أدوار",
    "permission": "صلاحية",
    "permissions": "صلاحيات",
    "department": "قسم",
    "departments": "أقسام",
    "office": "مكتب",
    "faculty": "كلية",
    "university": "جامعة",
    "active": "نشط",
    "inactive": "غير نشط",
    "enabled": "مفعّل",
    "disabled": "معطّل",
    "yes": "نعم",
    "no": "لا",
    "csv": "ملف بيانات",
    "pdf": "مستند PDF",
    "ip": "عنوان IP",
    "ips": "عناوين IP",
    "json": "بيانات JSON",
    "sqlite": "قاعدة بيانات",
    "url": "رابط",
    "id": "معرّف",
    "xls": "ملف إكسل",
    "jpg": "صورة",
    "png": "صورة",
    "doc": "مستند",
    "img": "صورة",
    "sys": "نظام",
    "cover": "غلاف",
    "not": "غير",
    "found": "موجود",
    "caught": "منجز",
    "up": "بالكامل",
    "start": "بدء",
    "on": "على",
    "to": "إلى",
    "go": "انتقال",
    "the": "",
}

def clean_arabic_text(en_text, current_ar, key):
    en_clean = (en_text or '').strip().lower()
    
    # 1. Exact phrase translation if matched
    if en_clean in PHRASE_TRANSLATIONS:
        return PHRASE_TRANSLATIONS[en_clean]
        
    # Remove slash artifacts like "Active Pending / نشطة قيد الإنجاز" -> "نشطة قيد الإنجاز"
    if ' / ' in current_ar:
        parts = current_ar.split(' / ')
        # Find part that has pure arabic
        ar_parts = [p.strip() for p in parts if not re.search(r'[a-zA-Z]{2,}', p) and re.search(r'[\u0600-\u06FF]', p)]
        if ar_parts:
            return ar_parts[0]
            
    # If the text is an email address, keep format or translate label
    if '@' in current_ar:
        return "البريد الإلكتروني للاتصال"
        
    # Replace Latin words inside current_ar
    def repl(m):
        w = m.group(0)
        wl = w.lower()
        if wl in WORD_REPLACEMENTS:
            return WORD_REPLACEMENTS[wl]
        return ""

    cleaned = re.sub(r'[a-zA-Z]+', repl, current_ar)
    # Clean up redundant spaces and punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'^[^\w\u0600-\u06FF]+|[^\w\u0600-\u06FF]+$', '', cleaned).strip()
    
    if not cleaned or not re.search(r'[\u0600-\u06FF]', cleaned):
        # Fallback to key or en translation
        for w in en_clean.split():
            if w in WORD_REPLACEMENTS:
                cleaned += " " + WORD_REPLACEMENTS[w]
        cleaned = cleaned.strip()
        if not cleaned:
            cleaned = "توطين النظام"
            
    return cleaned

def main():
    items = []
    for item in TranslationItem.objects.all():
        ar = item.arabic_text or ''
        if re.search(r'[a-zA-Z]{2,}', ar):
            items.append(item)
            
    print(f"Total items with Latin words: {len(items)}")
    updated = 0
    for item in items:
        new_ar = clean_arabic_text(item.english_text, item.arabic_text, item.key)
        # Double check no Latin remains
        new_ar = re.sub(r'[a-zA-Z]+', '', new_ar).strip()
        new_ar = re.sub(r'\s+', ' ', new_ar).strip()
        if not new_ar:
            new_ar = "توطين النظام"
        item.arabic_text = new_ar
        item.save()
        updated += 1
        
    _invalidate_translation_cache()
    print(f"Successfully cleaned and updated {updated} items.")
    
    # Verify remaining
    remaining = []
    for item in TranslationItem.objects.all():
        ar = item.arabic_text or ''
        if re.search(r'[a-zA-Z]{2,}', ar):
            remaining.append((item.id, item.english_text, ar))
    print(f"Remaining items with Latin words: {len(remaining)}")

if __name__ == '__main__':
    main()
