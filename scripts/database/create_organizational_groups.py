#!/usr/bin/env python
"""
Create the 11 Academic Organizational Groups and their respective Modules / Structures.
Target Institution: Faculty of Law and Political Science — University of Ghardaia
(كلية الحقوق والعلوم السياسية — جامعة غرداية)
"""
import os
import sys
import django

# Setup Django Environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from users.models import CustomUser
from work_modules.models import WorkGroup, WorkModule

def run():
    print("═" * 65)
    print("  CREATING THE 11 ACADEMIC ORGANIZATIONAL GROUPS & STRUCTURES")
    print("═" * 65)

    admin_user = (
        CustomUser.objects.filter(is_superuser=True).first() or
        CustomUser.objects.filter(role='super_admin').first() or
        CustomUser.objects.first()
    )
    if not admin_user:
        print("[!] No administrative user found. Aborting.")
        return

    print(f"[*] Admin owner for created modules: {admin_user.username} ({admin_user.email})")

    ORGANIZATIONAL_STRUCTURE = [
        {
            "order": 1,
            "name": "العمادة — Dean's Office",
            "slug": "deans-office",
            "description": "الهيكل الإداري والقيادي لعمادة الكلية ومتابعة القرارات الإستراتيجية والتسيير العام.",
            "icon_class": "fa-university",
            "color": "#991b1b", # Crimson / Dean's Red
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "عميد الكلية",
                    "slug": "deans-office-dean",
                    "icon": "fa-user-tie",
                    "color": "#991b1b",
                    "description": "مكتب عميد الكلية - الإشراف العام، اتخاذ القرارات والتمثيل المؤسسي الرسمي."
                },
                {
                    "name": "الأمانة الخاصة بالعميد",
                    "slug": "deans-office-secretariat",
                    "icon": "fa-user-shield",
                    "color": "#b91c1c",
                    "description": "الأمانة الخاصة بالعميد - تنظيم المواعيد، البريد السري، والتنسيق المباشر."
                }
            ]
        },
        {
            "order": 2,
            "name": "نيابة العمادة المكلفة بالدراسات وشؤون الطلبة",
            "slug": "vice-dean-studies-students",
            "description": "متابعة المسار البيداغوجي، شؤون الطلبة، التدريس والتقييم، والشهادات والنتائج.",
            "icon_class": "fa-user-graduate",
            "color": "#2563eb", # Royal Blue
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "نائب العميد للدراسات وشؤون الطلبة",
                    "slug": "vice-dean-studies",
                    "icon": "fa-user-graduate",
                    "color": "#2563eb",
                    "description": "مكتب نائب العميد المكلف بالدراسات والمسائل المرتبطة بالطلبة والتنظيم البيداغوجي."
                },
                {
                    "name": "مصلحة التدريس والتعليم والتقييم",
                    "slug": "service-teaching-evaluation",
                    "icon": "fa-chalkboard-teacher",
                    "color": "#3b82f6",
                    "description": "تنظيم ومتابعة جداول التوقيت، الامتحانات، وعمليات التقييم المستمر."
                },
                {
                    "name": "مصلحة متابعة التعليم والتنسيق البيداغوجي",
                    "slug": "service-pedagogical-coordination",
                    "icon": "fa-tasks",
                    "color": "#1d4ed8",
                    "description": "التنسيق البيداغوجي بين الأقسام، متابعة البرامج ومشاريع التكوين المعتمدة."
                },
                {
                    "name": "مصلحة الشهادات والنتائج",
                    "slug": "service-diplomas-results",
                    "icon": "fa-award",
                    "color": "#60a5fa",
                    "description": "إصدار كشوف النقاط، المداولات السنوية، والشهادات الجامعية المؤقتة والنهائية."
                }
            ]
        },
        {
            "order": 3,
            "name": "نيابة العمادة المكلفة بما بعد التدرج والبحث العلمي والعلاقات الخارجية",
            "slug": "vice-dean-postgrad-research",
            "description": "إدارة الدراسات العليا، التكوين في الدكتوراه، البحث العلمي، والتعاون الدولي والخارجي.",
            "icon_class": "fa-microscope",
            "color": "#7c3aed", # Purple
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "نائب العميد لما بعد التدرج والبحث العلمي",
                    "slug": "vice-dean-postgrad",
                    "icon": "fa-microscope",
                    "color": "#7c3aed",
                    "description": "مكتب نائب العميد المكلف بما بعد التدرج والبحث العلمي والعلاقات الخارجية."
                },
                {
                    "name": "مصلحة متابعة التكوين في الدكتوراه",
                    "slug": "service-phd-training",
                    "icon": "fa-graduation-cap",
                    "color": "#8b5cf6",
                    "description": "متابعة تسجيلات وطلبة الدكتوراه، لجان الأطروحات، والتأهيل الجامعي."
                },
                {
                    "name": "مصلحة البحث العلمي",
                    "slug": "service-scientific-research",
                    "icon": "fa-atom",
                    "color": "#6d28d9",
                    "description": "تنظيم الملتقيات العلمية، متابعة المشاريع والمجلات الأكاديمية المصنفة."
                },
                {
                    "name": "مصلحة العلاقات الخارجية والتعاون",
                    "slug": "service-external-relations",
                    "icon": "fa-globe-africa",
                    "color": "#a78bfa",
                    "description": "إبرام اتفاقيات التبادل العلمي، التداريب الخارجية، وبرامج التعاون الدولي."
                }
            ]
        },
        {
            "order": 4,
            "name": "الأمانة العامة — General Secretariat",
            "slug": "general-secretariat",
            "description": "التسيير الإداري والمالي، شؤون المستخدمين، الميزانية والمحاسبة، والوسائل العامة والصيانة.",
            "icon_class": "fa-building",
            "color": "#059669", # Emerald Green
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "الأمين العام للكلية",
                    "slug": "general-secretary",
                    "icon": "fa-building",
                    "color": "#059669",
                    "description": "مكتب الأمين العام - الإشراف على المصالح الإدارية والمالية وتنسيق المصالح المشتركة."
                },
                {
                    "name": "مصلحة المستخدمين",
                    "slug": "service-personnel-hr",
                    "icon": "fa-users-cog",
                    "color": "#10b981",
                    "description": "المسار المهني للأساتذة والموظفين الإداريين والتقنيين والترقيات والتوظيف."
                },
                {
                    "name": "مصلحة الميزانية والمحاسبة",
                    "slug": "service-budget-accounting",
                    "icon": "fa-file-invoice-dollar",
                    "color": "#047857",
                    "description": "تنفيذ ميزانية التسيير، إعداد الرواتب، وتتبع العمليات المالية والمحاسبية."
                },
                {
                    "name": "مصلحة الوسائل والصيانة",
                    "slug": "service-logistics-maintenance",
                    "icon": "fa-tools",
                    "color": "#34d399",
                    "description": "صيانة المرافق، شبكات الكهرباء والماء، وإدارة المخزون واللوازم المكتبية."
                }
            ]
        },
        {
            "order": 5,
            "name": "قسم الحقوق — Department of Law",
            "slug": "department-of-law",
            "description": "التسيير البيداغوجي والأكاديمي لقسم الحقوق، اللجان العلمية ومسؤولو التخصصات.",
            "icon_class": "fa-balance-scale",
            "color": "#b45309", # Amber Law Gold
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "رئيس قسم الحقوق",
                    "slug": "head-department-law",
                    "icon": "fa-balance-scale",
                    "color": "#b45309",
                    "description": "إدارة قسم الحقوق والإشراف على السير الحسن للمساقات والأساتذة."
                },
                {
                    "name": "أمانة قسم الحقوق",
                    "slug": "secretariat-department-law",
                    "icon": "fa-briefcase",
                    "color": "#d97706",
                    "description": "الأمانة الإدارية لقسم الحقوق، استقبال المراسلات وتنظيم الملفات."
                },
                {
                    "name": "اللجنة العلمية لقسم الحقوق",
                    "slug": "scientific-committee-law",
                    "icon": "fa-scroll",
                    "color": "#92400e",
                    "description": "اللجنة العلمية للقسم - البت في مشاريع التكوين ومواضيع المذكرات والمقاييس."
                },
                {
                    "name": "مسؤولو التخصصات — قسم الحقوق",
                    "slug": "speciality-coordinators-law",
                    "icon": "fa-sitemap",
                    "color": "#f59e0b",
                    "description": "تنسيق مسارات ليسانس وماستر في القانون العام والقانون الخاص."
                }
            ]
        },
        {
            "order": 6,
            "name": "قسم العلوم السياسية — Department of Political Science",
            "slug": "department-of-political-science",
            "description": "التسيير البيداغوجي والأكاديمي لقسم العلوم السياسية والعلاقات الدولية.",
            "icon_class": "fa-landmark",
            "color": "#0284c7", # Sky Blue
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "رئيس قسم العلوم السياسية",
                    "slug": "head-department-pol-sci",
                    "icon": "fa-landmark",
                    "color": "#0284c7",
                    "description": "إدارة قسم العلوم السياسية والإشراف على البرامج الأكاديمية والأساتذة."
                },
                {
                    "name": "أمانة قسم العلوم السياسية",
                    "slug": "secretariat-department-pol-sci",
                    "icon": "fa-briefcase",
                    "color": "#0ea5e9",
                    "description": "الأمانة الإدارية لقسم العلوم السياسية وتتبع ملفات الطلبة."
                },
                {
                    "name": "اللجنة العلمية لقسم العلوم السياسية",
                    "slug": "scientific-committee-pol-sci",
                    "icon": "fa-scroll",
                    "color": "#0369a1",
                    "description": "اللجنة العلمية لدراسة المشاريع البحثية والبيداغوجية لقسم العلوم السياسية."
                },
                {
                    "name": "مسؤولو التخصصات — قسم العلوم السياسية",
                    "slug": "speciality-coordinators-pol-sci",
                    "icon": "fa-sitemap",
                    "color": "#38bdf8",
                    "description": "تنسيق التخصصات في التنظيم السياسي والإداري والعلاقات الدولية."
                }
            ]
        },
        {
            "order": 7,
            "name": "المجلس العلمي للكلية — Faculty Scientific Council",
            "slug": "faculty-scientific-council",
            "description": "الهيئة الاستشارية والعلمية العليا للكلية لمتابعة البرامج والتأهيل الجامعي والبحوث.",
            "icon_class": "fa-award",
            "color": "#c026d3", # Fuchsia
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "رئيس المجلس العلمي للكلية",
                    "slug": "president-scientific-council",
                    "icon": "fa-award",
                    "color": "#c026d3",
                    "description": "رئاسة دورات المجلس العلمي، إعداد جداول الأعمال والمصادقة على التوصيات."
                },
                {
                    "name": "أعضاء المجلس العلمي",
                    "slug": "members-scientific-council",
                    "icon": "fa-users",
                    "color": "#d946ef",
                    "description": "ممثلو الأقسام والأساتذة الباحثون أعضاء المجلس العلمي للكلية."
                }
            ]
        },
        {
            "order": 8,
            "name": "مخابر البحث العلمي — Research Laboratories",
            "slug": "research-laboratories",
            "description": "متابعة المشاريع البحثية، فرق البحث، والباحثين المعتمدين بالكلية.",
            "icon_class": "fa-flask",
            "color": "#0d9488", # Teal
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "مدير مخبر البحث",
                    "slug": "director-research-lab",
                    "icon": "fa-flask",
                    "color": "#0d9488",
                    "description": "إدارة مخبر البحث العلمي، إعداد الميزانية السنوية ومشاريع النشر الأكاديمي."
                },
                {
                    "name": "فرق البحث العلمي",
                    "slug": "research-teams",
                    "icon": "fa-project-diagram",
                    "color": "#14b8a6",
                    "description": "متابعة محاور ومشاريع فرق البحث PRFU والدراسات القانونية والسياسية."
                },
                {
                    "name": "الباحثون",
                    "slug": "faculty-researchers",
                    "icon": "fa-microscope",
                    "color": "#0f766e",
                    "description": "سجل الأساتذة الباحثين، نشر المقالات والمشاركات في الفعاليات الوطنية والدولية."
                }
            ]
        },
        {
            "order": 9,
            "name": "المكتبة — Library",
            "slug": "faculty-library",
            "description": "تسيير الرصيد الوثائقي، المراجع الأكاديمية، والخدمات المكتبية للأساتذة والطلبة.",
            "icon_class": "fa-book-reader",
            "color": "#ea580c", # Orange
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "مسؤول المكتبة",
                    "slug": "head-of-library",
                    "icon": "fa-book-reader",
                    "color": "#ea580c",
                    "description": "إدارة المكتبة، التزويد بالمراجع والكتب، ورقمنة الفهارس والمستودع الرقمي."
                },
                {
                    "name": "موظفو المكتبة",
                    "slug": "library-staff",
                    "icon": "fa-book-open",
                    "color": "#f97316",
                    "description": "خدمات الإعارة، قاعات المطالعة، والإيداع القانوني للمذكرات والأطروحات."
                }
            ]
        },
        {
            "order": 10,
            "name": "المصالح الداعمة — Support Services",
            "slug": "support-services",
            "description": "المصالح التقنية واللوجستية الداعمة: الإعلام الآلي، الأرشيف والمراسلات، والتجهيزات.",
            "icon_class": "fa-cogs",
            "color": "#475569", # Slate
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "مصلحة الإعلام الآلي",
                    "slug": "service-it-systems",
                    "icon": "fa-desktop",
                    "color": "#475569",
                    "description": "صيانة الشبكات الداخلية، إدارة الخوادم، البوابة الرقمية والدعم التقني المستمر."
                },
                {
                    "name": "مصلحة الأرشيف والمراسلات",
                    "slug": "service-archives-mail",
                    "icon": "fa-envelope-open-text",
                    "color": "#64748b",
                    "description": "أرشفة السجلات الرسمية، تتبع البريد الصادر والوارد وتسجيل المراسلات الإدارية."
                },
                {
                    "name": "مصلحة الوسائل والتجهيزات",
                    "slug": "service-equipment-logistics",
                    "icon": "fa-boxes",
                    "color": "#334155",
                    "description": "تسيير العتاد البيداغوجي، أجهزة العرض، القاعات والمدرجات والتجهيزات العامة."
                }
            ]
        },
        {
            "order": 11,
            "name": "الأمن والوقاية — Security and Safety",
            "slug": "security-and-safety",
            "description": "أمن وحماية المنشآت الجامعية، السلامة والوقاية، وفرق الحراسة الداخلية والخارجية.",
            "icon_class": "fa-shield-alt",
            "color": "#e11d48", # Rose Red
            "bg_color": "#ffffff",
            "modules": [
                {
                    "name": "مكتب الأمن والوقاية",
                    "slug": "office-security-safety",
                    "icon": "fa-shield-alt",
                    "color": "#e11d48",
                    "description": "مخطط الأمن الداخلي، وسائل إطفاء الحرائق والوقاية من الحوادث والمخاطر."
                },
                {
                    "name": "فرق الحراسة والسلامة",
                    "slug": "teams-guards-safety",
                    "icon": "fa-user-shield",
                    "color": "#f43f5e",
                    "description": "تأمين المداخل والمخارج، تسيير بطاقات الدخول ومراقبة الحرم الجامعي على مدار الساعة."
                }
            ]
        }
    ]

    total_groups_created = 0
    total_modules_created = 0

    for g_data in ORGANIZATIONAL_STRUCTURE:
        # Create or update WorkGroup
        group, g_created = WorkGroup.objects.get_or_create(
            slug=g_data["slug"],
            defaults={
                "name": g_data["name"],
                "description": g_data["description"],
                "icon_class": g_data["icon_class"],
                "color": g_data["color"],
                "bg_color": g_data["bg_color"],
                "order": g_data["order"],
            }
        )
        if not g_created:
            group.name = g_data["name"]
            group.description = g_data["description"]
            group.icon_class = g_data["icon_class"]
            group.color = g_data["color"]
            group.bg_color = g_data["bg_color"]
            group.order = g_data["order"]
            group.save()
            print(f"[✓] Updated WorkGroup #{group.order}: {group.name}")
        else:
            total_groups_created += 1
            print(f"[+] Created WorkGroup #{group.order}: {group.name}")

        # Attach admin user as member
        if admin_user not in group.members.all():
            group.members.add(admin_user)

        # Create sub-structure WorkModules for this group
        for mod_idx, m_data in enumerate(g_data["modules"], start=1):
            mod, m_created = WorkModule.objects.get_or_create(
                slug=m_data["slug"],
                defaults={
                    "name": m_data["name"],
                    "icon_class": m_data["icon"],
                    "color": m_data["color"],
                    "description": m_data["description"],
                    "creator": admin_user,
                    "group": group.name,
                    "group_link": group,
                    "order": mod_idx,
                    "is_shared": True,
                    "allow_enrollment": True
                }
            )
            if not m_created:
                mod.name = m_data["name"]
                mod.icon_class = m_data["icon"]
                mod.color = m_data["color"]
                mod.description = m_data["description"]
                mod.group = group.name
                mod.group_link = group
                mod.order = mod_idx
                mod.is_shared = True
                mod.save()
                print(f"    ├─ [✓] Updated Module: {mod.name}")
            else:
                total_modules_created += 1
                print(f"    ├─ [+] Created Module: {mod.name}")

    print("═" * 65)
    print(f"[DONE] Total WorkGroups in DB: {WorkGroup.objects.count()}")
    print(f"[DONE] Total WorkModules in DB: {WorkModule.objects.count()}")
    print("═" * 65)

if __name__ == '__main__':
    run()
