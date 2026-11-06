"""
Faculty of Law and Political Science - University of Ghardaia
Database Reset & Faculty Structure Seeder Engine (Comprehensive Edition)
========================================================================
Provides complete reset and realistic academic enterprise data population:
1. 5 Official Work Groups with custom aesthetics
2. 20 Faculty Modules with default banner images, lifecycle dates across 2026, and progress
3. Faculty Staff Users (Dean, SG, Vice Deans, Dept Heads, Officers)
4. Comprehensive Tasks for EVERY module with real descriptions, October 2026 deadlines,
   and exact Ghardaia University campus GPS coordinates
5. Submissions for every task dated in October 2026 (Approved, Rejected, Under Review, Submitted)
6. Peer-to-peer Messaging: Every user exchanges at least 10 back-and-forth messages with 7+ colleagues
7. In-App Notifications for tasks, submissions, reviews, and reminders
8. Daily Attendance Records for staff
"""

import os
import random
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from work_modules.models import WorkGroup, WorkModule
from tasks.models import Task, Tag
from submissions.models import Submission, SubmissionComment
from messaging.models import Conversation, ConversationMember, Message
from attendance.models import AttendanceRecord
from notifications.models import Notification
from core.models import SiteConfiguration

User = get_user_model()

DEFAULT_BANNER_PATH = "module_banners/faculty_default_banner.jpeg"
DEFAULT_COVER_PATH = "task_covers/faculty_default_banner.jpeg"

# Official University of Ghardaia Faculty Structure
FACULTY_GROUPS = [
    {
        "name": "1. مجموعة الإدارة العليا والقيادة",
        "slug": "management-leadership",
        "description": "عمادة الكلية، الأمانة العامة، ومكتب السكرتارية والخلية التنفيذية لقيادة الكلية والتنسيق العام.",
        "icon_class": "fa-chess-king",
        "color": "#b91c1c",
        "bg_color": "#fff5f5",
        "order": 1,
        "modules": [
            {
                "name": "عميد الكلية",
                "slug": "doyen-faculte",
                "icon_class": "fa-user-tie",
                "color": "#dc2626",
                "description": "مكتب عميد كلية الحقوق والعلوم السياسية، التوجيه الاستراتيجي والقرارات العليا والتمثيل الرسمي.",
                "order": 1,
                "start_date": date(2026, 1, 2),
                "deadline": date(2026, 12, 31),
                "progress": 85,
                "lat": 32.4845,
                "lng": 3.6685,
                "loc_name": "مبنى عمادة كلية الحقوق - مجمع نوميرات، غرداية",
            },
            {
                "name": "الأمانة العامة للكلية",
                "slug": "secretariat-general",
                "icon_class": "fa-briefcase",
                "color": "#b91c1c",
                "description": "الإشراف الإداري والمالي العام على مصالح الكلية وتسيير العمليات اللوجستية.",
                "order": 2,
                "start_date": date(2026, 1, 2),
                "deadline": date(2026, 12, 31),
                "progress": 80,
                "lat": 32.4842,
                "lng": 3.6682,
                "loc_name": "مقر الأمانة العامة - الجناح الإداري، نوميرات، غرداية",
            },
            {
                "name": "مكتب السكرتارية والخلية التنفيذية",
                "slug": "secretariat-executif",
                "icon_class": "fa-clipboard-check",
                "color": "#991b1b",
                "description": "معالجة البريد الوارد والصادر، التنسيق التنفيذي، وتنظيم جدول أعمال الإدارة والاجتماعات.",
                "order": 3,
                "start_date": date(2026, 1, 5),
                "deadline": date(2026, 12, 31),
                "progress": 90,
                "lat": 32.4844,
                "lng": 3.6684,
                "loc_name": "مكتب السكرتارية التنفيذية - مبنى العمادة، غرداية",
            },
        ],
    },
    {
        "name": "2. مجموعة الشؤون البيداغوجية والتعليمية",
        "slug": "pedagogical-educational-affairs",
        "description": "نيابة العمادة للدراسات وشؤون الطلبة، أقسام الحقوق والعلوم السياسية والتكوين والتقييم.",
        "icon_class": "fa-graduation-cap",
        "color": "#2563eb",
        "bg_color": "#eff6ff",
        "order": 2,
        "modules": [
            {
                "name": "مصلحة التسجيلات والتوجيه",
                "slug": "service-inscriptions-orientation",
                "icon_class": "fa-user-check",
                "color": "#3b82f6",
                "description": "استقبال وتسجيل الطلبة الجدد (ليسانس وماستر)، التوجيه البيداغوجي، والتحويلات الجامعية.",
                "order": 1,
                "start_date": date(2026, 7, 15),
                "deadline": date(2026, 10, 31),
                "progress": 95,
                "lat": 32.4834,
                "lng": 3.6674,
                "loc_name": "شبابيك التسجيلات والتوجيه - القطب الجامعي نوميرات، غرداية",
            },
            {
                "name": "مصلحة التعليم والتقييم",
                "slug": "service-enseignement-evaluation",
                "icon_class": "fa-chalkboard-teacher",
                "color": "#2563eb",
                "description": "برمجة الجداول البيداغوجية، تنظيم الامتحانات، حساب الأرصدة والمداولات في نظام LMD.",
                "order": 2,
                "start_date": date(2026, 9, 1),
                "deadline": date(2027, 2, 15),
                "progress": 68,
                "lat": 32.4836,
                "lng": 3.6676,
                "loc_name": "مكتب التعليم والتقييم البيداغوجي - كلية الحقوق، غرداية",
            },
            {
                "name": "مصلحة الشهادات والمسار المهني",
                "slug": "service-diplomes-parcours",
                "icon_class": "fa-award",
                "color": "#1d4ed8",
                "description": "إعداد وتدقيق شهادات التخرج وكشوف النقاط والمطابقة مع السجلات الرسمية.",
                "order": 3,
                "start_date": date(2026, 6, 1),
                "deadline": date(2026, 11, 30),
                "progress": 82,
                "lat": 32.4837,
                "lng": 3.6677,
                "loc_name": "مصلحة تسليم الشهادات والمسار - القطب 1، نوميرات، غرداية",
            },
            {
                "name": "قسم الحقوق (القانون العام والقانون الخاص)",
                "slug": "dept-droit",
                "icon_class": "fa-balance-scale",
                "color": "#1e40af",
                "description": "إدارة شعبة الحقوق بتخصصاتها (قانون جنائي، قانون إداري، قانون أعمال، قانون دولي عام).",
                "order": 4,
                "start_date": date(2026, 9, 1),
                "deadline": date(2027, 6, 30),
                "progress": 72,
                "lat": 32.4835,
                "lng": 3.6675,
                "loc_name": "مبنى قسم الحقوق - مجمع المدرجات، نوميرات، غرداية",
            },
            {
                "name": "قسم العلوم السياسية (التنظيمات والعلاقات الدولية)",
                "slug": "dept-sciences-politiques",
                "icon_class": "fa-landmark",
                "color": "#172554",
                "description": "إدارة شعبة العلوم السياسية وتخصصات العلاقات الدولية والتنظيمات الإدارية والسياسات العامة.",
                "order": 5,
                "start_date": date(2026, 9, 1),
                "deadline": date(2027, 6, 30),
                "progress": 70,
                "lat": 32.4830,
                "lng": 3.6670,
                "loc_name": "مبنى قسم العلوم السياسية - مجمع نوميرات، غرداية",
            },
        ],
    },
    {
        "name": "3. مجموعة البحث العلمي والتعاون الخارجي",
        "slug": "scientific-research-cooperation",
        "description": "نيابة العمادة لما بعد التدرج، متابعة أطروحات الدكتوراه، المخابر والمجلس العلمي.",
        "icon_class": "fa-microscope",
        "color": "#059669",
        "bg_color": "#ecfdf5",
        "order": 3,
        "modules": [
            {
                "name": "مصلحة ما بعد التدرج (متابعة طور الدكتوراه)",
                "slug": "service-post-graduation-doctorat",
                "icon_class": "fa-user-graduate",
                "color": "#10b981",
                "description": "متابعة مسار طلبة الدكتوراه (LMD والعلوم)، تراخيص المناقشات، وتقارير القابلية.",
                "order": 1,
                "start_date": date(2026, 9, 15),
                "deadline": date(2027, 6, 30),
                "progress": 62,
                "lat": 32.4855,
                "lng": 3.6702,
                "loc_name": "مركز الدكتوراه وما بعد التدرج - كلية الحقوق، غرداية",
            },
            {
                "name": "مصلحة البحث العلمي وتطوير التكنولوجيات",
                "slug": "service-recherche-technologies",
                "icon_class": "fa-atom",
                "color": "#059669",
                "description": "اعتماد وتمويل مشاريع البحث الجامعي PRFU، والمنشورات العلمية المفهرسة.",
                "order": 2,
                "start_date": date(2026, 1, 10),
                "deadline": date(2026, 12, 20),
                "progress": 76,
                "lat": 32.4858,
                "lng": 3.6705,
                "loc_name": "مكتب مشاريع البحث العلمي PRFU - جامعة غرداية",
            },
            {
                "name": "مصلحة التعاون والاتصال والعلاقات الخارجية",
                "slug": "service-cooperation-relations-ext",
                "icon_class": "fa-globe-africa",
                "color": "#047857",
                "description": "اتفاقيات التعاون والشراكة مع الهيئات القضائية والجامعات الوطنية والدولية والتظاهرات العلمية.",
                "order": 3,
                "start_date": date(2026, 2, 1),
                "deadline": date(2026, 12, 15),
                "progress": 72,
                "lat": 32.4850,
                "lng": 3.6695,
                "loc_name": "مكتب التعاون الدولي والشراكات - رئاسة الكلية، غرداية",
            },
            {
                "name": "المجلس العلمي للكلية",
                "slug": "conseil-scientifique-faculte",
                "icon_class": "fa-users-cog",
                "color": "#065f46",
                "description": "دراسة ملفات التأهيل الجامعي ومشاريع فتح التخصصات والبرامج العلمية والترقيات.",
                "order": 4,
                "start_date": date(2026, 1, 15),
                "deadline": date(2026, 12, 15),
                "progress": 84,
                "lat": 32.4846,
                "lng": 3.6686,
                "loc_name": "قاعة اجتماعات المجلس العلمي - الطابق الثاني، كلية الحقوق",
            },
            {
                "name": "المخابر ووحدات البحث العلمي",
                "slug": "laboratoires-unites-recherche",
                "icon_class": "fa-flask",
                "color": "#064e3b",
                "description": "تنسيق أنشطة مخبر الدراسات القانونية والقضائية ومخبر التحولات السياسية والإدارية.",
                "order": 5,
                "start_date": date(2026, 1, 2),
                "deadline": date(2026, 12, 31),
                "progress": 78,
                "lat": 32.4862,
                "lng": 3.6710,
                "loc_name": "مجمع مخابر البحث العلمي القانوني - جامعة غرداية",
            },
        ],
    },
    {
        "name": "4. مجموعة الدعم الإداري والتقني",
        "slug": "administrative-technical-support",
        "description": "الموارد البشرية والموظفون، الميزانية والمالية، الصيانة والوسائل العامة والإعلام الآلي.",
        "icon_class": "fa-cogs",
        "color": "#7c3aed",
        "bg_color": "#f5f3ff",
        "order": 4,
        "modules": [
            {
                "name": "مصلحة الموظفين والموارد البشرية",
                "slug": "service-personnel-rh",
                "icon_class": "fa-id-card",
                "color": "#8b5cf6",
                "description": "تسيير المسار الإداري للأساتذة والموظفين، الإجازات، التأمينات والترقيات المهنية.",
                "order": 1,
                "start_date": date(2026, 1, 2),
                "deadline": date(2026, 12, 31),
                "progress": 88,
                "lat": 32.4841,
                "lng": 3.6681,
                "loc_name": "مصلحة المستخدمين والموارد البشرية - الجناح المركزي، غرداية",
            },
            {
                "name": "مصلحة الميزانية والمالية",
                "slug": "service-budget-finances",
                "icon_class": "fa-coins",
                "color": "#7c3aed",
                "description": "إعداد ميزانية التسيير، متابعة الالتزامات المالية، وصرف مستحقات الأساتذة والمؤطرين.",
                "order": 2,
                "start_date": date(2026, 1, 2),
                "deadline": date(2026, 12, 31),
                "progress": 85,
                "lat": 32.4842,
                "lng": 3.6682,
                "loc_name": "مصلحة الميزانية والمحاسبة - مجمع نوميرات، غرداية",
            },
            {
                "name": "مصلحة الصيانة والوسائل العامة",
                "slug": "service-moyens-generaux-maintenance",
                "icon_class": "fa-tools",
                "color": "#6d28d9",
                "description": "صيانة القاعات والمدرجات، توفير التجهيزات المكتبية، والأمن والسلامة المهنية.",
                "order": 3,
                "start_date": date(2026, 2, 1),
                "deadline": date(2026, 11, 30),
                "progress": 75,
                "lat": 32.4858,
                "lng": 3.6715,
                "loc_name": "مصلحة الوسائل العامة والورشات - القطب 1، نوميرات، غرداية",
            },
            {
                "name": "مصلحة الإعلام الآلي والراديوي والإحصاء",
                "slug": "service-informatique-statistiques",
                "icon_class": "fa-network-wired",
                "color": "#5b21b6",
                "description": "إدارة الشبكة الجامعية، المخدمات المحلية، رقمنة العمليات البيداغوجية، والإحصائيات.",
                "order": 4,
                "start_date": date(2026, 1, 5),
                "deadline": date(2026, 12, 25),
                "progress": 92,
                "lat": 32.4848,
                "lng": 3.6688,
                "loc_name": "مركز البيانات والشبكات - كلية الحقوق، نوميرات، غرداية",
            },
        ],
    },
    {
        "name": "5. مجموعة المرافق والخدمات العلمية المساعدة",
        "slug": "facilities-auxiliary-services",
        "description": "المكتبة المركزية للكلية، قاعة المحاكمات الافتراضية، والنوادي والجمعيات العلمية الطلابية.",
        "icon_class": "fa-university",
        "color": "#ea580c",
        "bg_color": "#fff7ed",
        "order": 5,
        "modules": [
            {
                "name": "مكتبة الكلية (قاعات المطالعة والأرشيف)",
                "slug": "bibliotheque-faculte-archives",
                "icon_class": "fa-book-reader",
                "color": "#f97316",
                "description": "إعارة المراجع والكتب القانونية، قاعات مطالعة الأساتذة والطلبة، ورقمنة الرسائل الجامعية.",
                "order": 1,
                "start_date": date(2026, 9, 1),
                "deadline": date(2027, 6, 30),
                "progress": 80,
                "lat": 32.4851,
                "lng": 3.6690,
                "loc_name": "مكتبة كلية الحقوق والعلوم السياسية - قاعة المطالعة الكبرى، غرداية",
            },
            {
                "name": "قاعة المحاكمات الافتراضية",
                "slug": "tribunal-virtuel-moot-court",
                "icon_class": "fa-gavel",
                "color": "#ea580c",
                "description": "تدريب طلبة الحقوق والماستر على المرافعات وإجراءات المحاكم الصورية بالتنسيق مع مجلس قضاء غرداية.",
                "order": 2,
                "start_date": date(2026, 9, 15),
                "deadline": date(2026, 12, 20),
                "progress": 85,
                "lat": 32.4839,
                "lng": 3.6678,
                "loc_name": "قاعة المحاكمات الافتراضية - الجناح القضائي الأكاديمي، غرداية",
            },
            {
                "name": "النوادي والجمعيات العلمية الطلابية",
                "slug": "clubs-associations-scientifiques",
                "icon_class": "fa-users",
                "color": "#c2410c",
                "description": "رعاية الأنشطة الثقافية والقانونية والمناظرات الفكرية لنوادي كلية الحقوق والعلوم السياسية.",
                "order": 3,
                "start_date": date(2026, 10, 1),
                "deadline": date(2027, 5, 30),
                "progress": 60,
                "lat": 32.4828,
                "lng": 3.6660,
                "loc_name": "فضاء الأنشطة الطلابية والنوادي العلمية - القطب 1، غرداية",
            },
        ],
    },
]

# Real Faculty Users
FACULTY_USERS_DATA = [
    {
        "email": "doyen.fdsp@univ-ghardaia.dz",
        "first_name": "أ.د. حميد",
        "last_name": "لزهر",
        "role": "manager",
        "theme": "light",
        "group_slugs": ["management-leadership", "scientific-research-cooperation"],
    },
    {
        "email": "sg.fdsp@univ-ghardaia.dz",
        "first_name": "د. يوسف",
        "last_name": "بن براهيم",
        "role": "manager",
        "theme": "light",
        "group_slugs": ["management-leadership", "administrative-technical-support"],
    },
    {
        "email": "vicedoyen.pedagogie@univ-ghardaia.dz",
        "first_name": "د. كمال",
        "last_name": "قرينات",
        "role": "manager",
        "theme": "light",
        "group_slugs": ["pedagogical-educational-affairs"],
    },
    {
        "email": "vicedoyen.postgrad@univ-ghardaia.dz",
        "first_name": "أ.د. عمار",
        "last_name": "حليلو",
        "role": "manager",
        "theme": "light",
        "group_slugs": ["scientific-research-cooperation"],
    },
    {
        "email": "head.droit@univ-ghardaia.dz",
        "first_name": "د. بشير",
        "last_name": "بالواعر",
        "role": "manager",
        "theme": "light",
        "group_slugs": ["pedagogical-educational-affairs", "facilities-auxiliary-services"],
    },
    {
        "email": "head.scpo@univ-ghardaia.dz",
        "first_name": "د. سليمان",
        "last_name": "بن يحي",
        "role": "manager",
        "theme": "light",
        "group_slugs": ["pedagogical-educational-affairs", "facilities-auxiliary-services"],
    },
    {
        "email": "rh.fdsp@univ-ghardaia.dz",
        "first_name": "أ. مريم",
        "last_name": "بابا عمر",
        "role": "worker",
        "theme": "light",
        "group_slugs": ["administrative-technical-support"],
    },
    {
        "email": "finances.fdsp@univ-ghardaia.dz",
        "first_name": "أ. عمر",
        "last_name": "كحيل",
        "role": "worker",
        "theme": "light",
        "group_slugs": ["administrative-technical-support"],
    },
    {
        "email": "scolarite.fdsp@univ-ghardaia.dz",
        "first_name": "أ. عبد الرزاق",
        "last_name": "بن ساسي",
        "role": "worker",
        "theme": "light",
        "group_slugs": ["pedagogical-educational-affairs"],
    },
    {
        "email": "informatique.fdsp@univ-ghardaia.dz",
        "first_name": "م. إلياس",
        "last_name": "بوحفص",
        "role": "worker",
        "theme": "light",
        "group_slugs": ["administrative-technical-support"],
    },
    {
        "email": "postgrad.fdsp@univ-ghardaia.dz",
        "first_name": "أ. سمير",
        "last_name": "بن زيان",
        "role": "worker",
        "theme": "light",
        "group_slugs": ["scientific-research-cooperation"],
    },
    {
        "email": "bibliotheque.fdsp@univ-ghardaia.dz",
        "first_name": "أ. ليلى",
        "last_name": "أولاد هدار",
        "role": "worker",
        "theme": "light",
        "group_slugs": ["facilities-auxiliary-services"],
    },
    {
        "email": "tribunal.fdsp@univ-ghardaia.dz",
        "first_name": "أ. مصطفى",
        "last_name": "بن صالح",
        "role": "worker",
        "theme": "light",
        "group_slugs": ["facilities-auxiliary-services"],
    },
    {
        "email": "secretariat.fdsp@univ-ghardaia.dz",
        "first_name": "أ. نادية",
        "last_name": "بلخير",
        "role": "worker",
        "theme": "light",
        "group_slugs": ["management-leadership"],
    },
]


def reset_and_seed_faculty(keep_user_id=None, empty_only=False):
    """
    Purges previous non-protected records and seeds the complete Faculty of Law &
    Political Science data structure for University of Ghardaia.
    """
    with transaction.atomic():
        # 1. Identify and protect the single super admin
        super_admin = None
        if keep_user_id:
            super_admin = User.objects.filter(id=keep_user_id).first()
        if not super_admin:
            super_admin = User.objects.filter(is_superuser=True).first()
        if not super_admin:
            super_admin = User.objects.filter(role='super_admin').first()
        if not super_admin:
            super_admin = User.objects.create_superuser(
                email="admin@univ-ghardaia.dz",
                password="AdminPassword2026!",
                first_name="مدير",
                last_name="المنظومة",
                role="super_admin",
                is_platform_admin=True,
            )
        else:
            super_admin.role = 'super_admin'
            super_admin.is_staff = True
            super_admin.is_superuser = True
            super_admin.is_platform_admin = True
            super_admin.save()


        # 2. Delete non-protected data
        # Submissions & comments
        SubmissionComment.objects.all().delete()
        Submission.objects.all().delete()

        # Tasks
        Task.objects.all().delete()

        # Attendance & Notifications
        AttendanceRecord.objects.all().delete()
        Notification.objects.all().delete()

        # Messages & Conversations
        Message.objects.all().delete()
        ConversationMember.objects.all().delete()
        Conversation.objects.all().delete()

        # Delete custom modules except protected contact-submissions
        WorkModule.objects.exclude(slug='contact-submissions').delete()

        # Delete all existing WorkGroups
        WorkGroup.objects.all().delete()

        # Delete non-admin users
        User.objects.exclude(id=super_admin.id).delete()

        # Update Site Configuration branding
        site_cfg = SiteConfiguration.objects.first() or SiteConfiguration.objects.create()
        site_cfg.app_name = "جامعة غرداية - كلية الحقوق والعلوم السياسية"
        site_cfg.app_name_ar = "جامعة غرداية - كلية الحقوق والعلوم السياسية"
        site_cfg.primary_color = "#dc2626"
        site_cfg.banner_image = DEFAULT_BANNER_PATH
        site_cfg.save()

        if empty_only:
            return {
                "success": True,
                "status": "success",
                "mode": "empty_clean",
                "super_admin": super_admin.email,
                "users_count": 1,
                "modules_count": 1,
                "message": "تم تفريغ النظام بنجاح والإبقاء على مستخدم مسؤول واحد ووحدة الاتصال فقط."
            }

        # -------------------------------------------------------------
        # SEED FACULTY GROUPS, MODULES, USERS, TASKS, SUBMISSIONS & CHAT
        # -------------------------------------------------------------

        # Create Standard Tags
        tag_pedagogy, _ = Tag.objects.get_or_create(name="بيداغوجيا", defaults={"color": "#2563eb"})
        tag_exams, _ = Tag.objects.get_or_create(name="امتحانات ومداولات", defaults={"color": "#dc2626"})
        tag_research, _ = Tag.objects.get_or_create(name="بحث علمي ودكتوراه", defaults={"color": "#059669"})
        tag_admin, _ = Tag.objects.get_or_create(name="إدارة وأمانة عامة", defaults={"color": "#b91c1c"})
        tag_budget, _ = Tag.objects.get_or_create(name="مالية وميزانية", defaults={"color": "#d97706"})
        tag_legal, _ = Tag.objects.get_or_create(name="محاكمة صورية واستشارات", defaults={"color": "#7c3aed"})
        tag_digit, _ = Tag.objects.get_or_create(name="رقمنة وإعلام آلي", defaults={"color": "#0891b2"})

        # A. Create Faculty Users
        created_users = {}
        for u_data in FACULTY_USERS_DATA:
            u = User.objects.create_user(
                email=u_data["email"],
                password="Faculty2026!",
                first_name=u_data["first_name"],
                last_name=u_data["last_name"],
                role=u_data["role"],
                theme=u_data.get("theme", "light"),
                language="ar",
                admin_owner=super_admin,
                is_platform_admin=False,
            )
            created_users[u_data["email"]] = u

        dean = created_users["doyen.fdsp@univ-ghardaia.dz"]
        sg = created_users["sg.fdsp@univ-ghardaia.dz"]
        vd_ped = created_users["vicedoyen.pedagogie@univ-ghardaia.dz"]
        vd_post = created_users["vicedoyen.postgrad@univ-ghardaia.dz"]
        head_law = created_users["head.droit@univ-ghardaia.dz"]
        head_scpo = created_users["head.scpo@univ-ghardaia.dz"]
        user_rh = created_users["rh.fdsp@univ-ghardaia.dz"]
        user_fin = created_users["finances.fdsp@univ-ghardaia.dz"]
        user_scol = created_users["scolarite.fdsp@univ-ghardaia.dz"]
        user_it = created_users["informatique.fdsp@univ-ghardaia.dz"]
        user_post = created_users["postgrad.fdsp@univ-ghardaia.dz"]
        user_bib = created_users["bibliotheque.fdsp@univ-ghardaia.dz"]
        user_trib = created_users["tribunal.fdsp@univ-ghardaia.dz"]
        user_sec = created_users["secretariat.fdsp@univ-ghardaia.dz"]

        all_staff_list = [
            dean, sg, vd_ped, vd_post, head_law, head_scpo,
            user_rh, user_fin, user_scol, user_it, user_post,
            user_bib, user_trib, user_sec
        ]

        # B. Create Work Groups and Modules
        created_modules = {}
        created_groups = {}

        for g_data in FACULTY_GROUPS:
            group = WorkGroup.objects.create(
                name=g_data["name"],
                slug=g_data["slug"],
                description=g_data["description"],
                icon_class=g_data["icon_class"],
                color=g_data["color"],
                bg_color=g_data["bg_color"],
                order=g_data["order"],
            )
            created_groups[g_data["slug"]] = group

            # Add relevant members to group
            for u_data in FACULTY_USERS_DATA:
                if g_data["slug"] in u_data["group_slugs"]:
                    u_obj = created_users.get(u_data["email"])
                    if u_obj:
                        group.members.add(u_obj)
            group.members.add(super_admin)

            # Create Modules in this group
            for m_data in g_data["modules"]:
                module = WorkModule.objects.create(
                    name=m_data["name"],
                    slug=m_data["slug"],
                    icon_class=m_data["icon_class"],
                    color=m_data["color"],
                    description=m_data["description"],
                    group_link=group,
                    group=group.name,
                    order=m_data["order"],
                    banner_image=DEFAULT_BANNER_PATH,
                    is_shared=True,
                    allow_enrollment=True,
                    creator=dean,
                    start_date=m_data.get("start_date", date(2026, 9, 1)),
                    deadline=m_data.get("deadline", date(2026, 12, 31)),
                    progress=m_data.get("progress", 75),
                )
                module.allowed_admins.add(dean, sg, super_admin)
                for mem in group.members.all():
                    module.enrolled_users.add(mem)
                created_modules[m_data["slug"]] = module

        # C. Create Tasks for EVERY Module in Ghardaia with Submissions in October 2026
        now = timezone.now()

        # Detailed Task Definitions for each of the 20 modules
        tasks_raw_data = [
            # Group 1: Management & Leadership
            {
                "module": "doyen-faculte",
                "title": "متابعة مخرجات اجتماع مجلس الكلية الاستثنائي والمصادقة على محضر الجلسة",
                "desc": "دراسة التوصيات والمصادقة النهائية على محضر اجتماع مجلس كلية الحقوق والعلوم السياسية بخصوص التحضير للسداسي الثاني واعتماد لجان المناقشة.",
                "creator": dean, "assigned": [user_sec, sg],
                "priority": "critical", "type": "correspondence", "corr_type": "decision", "ref": "ق.إ/ع.ك/2026/08",
                "start": date(2026, 10, 2), "deadline": timezone.make_aware(datetime(2026, 10, 29, 16, 30)),
                "status": "in_progress", "progress": 80, "tags": [tag_admin],
                "lat": 32.4845, "lng": 3.6685, "loc_name": "مكتب عميد الكلية - مجمع نوميرات، غرداية",
                "sub_status": "submitted", "score": 90, "sub_date": datetime(2026, 10, 25, 11, 30),
                "sub_notes": "تمت صياغة المحضر ومراجعته مع السيد الأمين العام، مرفق للتوقيع والختم الإداري.",
                "feedback": "عمل ممتاز ومتقن، يُرسل لكافة الأقسام بعد التأشير."
            },
            {
                "module": "doyen-faculte",
                "title": "إعداد التقرير التوجيهي السنوي لمشاريع الكلية والشراكات الاستراتيجية 2026",
                "desc": "صياغة التقرير الشامل لعميد الكلية حول أداء الأقسام والمخابر والشراكات مع مجلس قضاء غرداية وغرفة التجارة والصناعة.",
                "creator": dean, "assigned": [sg, vd_ped, vd_post],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 5), "deadline": timezone.make_aware(datetime(2026, 11, 15, 14, 0)),
                "status": "completed", "progress": 100, "tags": [tag_admin, tag_research],
                "lat": 32.4845, "lng": 3.6685, "loc_name": "قاعة الاجتماعات الرسمية - عمادة الكلية، غرداية",
                "sub_status": "approved", "score": 98, "sub_date": datetime(2026, 10, 22, 16, 15),
                "sub_notes": "تم إنهاء صياغة التقرير الشامل مع الملاحق الإحصائية المعتمدة.",
                "feedback": "تقرير شامل ومتميز يعكس التطور الأكاديمي للكلية."
            },
            {
                "module": "secretariat-general",
                "title": "تقرير التدقيق المالي والإداري لنفقات التسيير والتجهيز الثلاثي الأول",
                "desc": "إعداد الكشف التفصيلي لنفقات تسيير الكلية وصيانة القاعات ومستلزمات التدريس المعتمدة في الميزانية الأولية.",
                "creator": sg, "assigned": [user_fin, user_rh],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 4), "deadline": timezone.make_aware(datetime(2026, 10, 31, 17, 0)),
                "status": "completed", "progress": 100, "tags": [tag_budget, tag_admin],
                "lat": 32.4842, "lng": 3.6682, "loc_name": "مقر الأمانة العامة - مجمع نوميرات، غرداية",
                "sub_status": "approved", "score": 96, "sub_date": datetime(2026, 10, 20, 10, 0),
                "sub_notes": "تم استكمال الجرد المالي وجدول النفقات الملتزم بها، الحسابات متطابقة مع أمين الخزينة.",
                "feedback": "تم التدقيق والمصادقة مع توجيه نسخة لمصالح رئاسة الجامعة."
            },
            {
                "module": "secretariat-general",
                "title": "مخطط الأمن والوقاية والصيانة الدورية للمرافق الجامعية للموسم الشتوي",
                "desc": "معاينة أجهزة التدفئة المركزية وعوازل الأسطح وأنظمة إطفاء الحرائق في كافة أجنحة الكلية ومدرجاتها.",
                "creator": sg, "assigned": [user_rh],
                "priority": "medium", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 8), "deadline": timezone.make_aware(datetime(2026, 11, 10, 15, 0)),
                "status": "in_progress", "progress": 65, "tags": [tag_admin],
                "lat": 32.4858, "lng": 3.6715, "loc_name": "أجنحة المدرجات والمرافق العامة - جامعة غرداية",
                "sub_status": "under_review", "score": None, "sub_date": datetime(2026, 10, 24, 14, 30),
                "sub_notes": "تم فحص المدرجات 1 و 2 و 3، والعمل جارٍ في القاعات البيداغوجية لقسم العلوم السياسية.",
                "feedback": "يرجى تسريع وتيرة العمل قبل دخول فصل الشتاء."
            },
            {
                "module": "secretariat-executif",
                "title": "أرشفة البريد الإداري والمراسلات الوزارية الصادرة والواردة لشهر أكتوبر 2026",
                "desc": "تسجيل المراسلات الرسمية في المنظومة الرقمية وتصنيفها حسب الأهمية وتوزيعها على المصالح المعنية.",
                "creator": sg, "assigned": [user_sec],
                "priority": "medium", "type": "correspondence", "corr_type": "memo", "ref": "م.ت/س.خ/2026/142",
                "start": date(2026, 10, 1), "deadline": timezone.make_aware(datetime(2026, 10, 31, 18, 0)),
                "status": "in_progress", "progress": 85, "tags": [tag_admin, tag_digit],
                "lat": 32.4844, "lng": 3.6684, "loc_name": "مكتب السكرتارية والبريد المركزي - كلية الحقوق، غرداية",
                "sub_status": "submitted", "score": 92, "sub_date": datetime(2026, 10, 26, 16, 0),
                "sub_notes": "تمت معالجة وأرشفة 185 مراسلة وإحالتها للمصالح المختصة عبر البوابة الرقمية.",
                "feedback": "متابعة دقيقة ومستمرة، واصلوا العمل."
            },

            # Group 2: Pedagogical & Educational Affairs
            {
                "module": "service-inscriptions-orientation",
                "title": "معالجة ملفات التحويلات الجامعية وتدقيق كشوف النقاط للطلبة المقبولين",
                "desc": "دراسة طلبات التحويل الداخلي والخارجي لطلبة الليسانس والماستر والتحقق من الشروط البيداغوجية ومطابقة النقاط.",
                "creator": vd_ped, "assigned": [user_scol],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 1), "deadline": timezone.make_aware(datetime(2026, 10, 28, 17, 0)),
                "status": "completed", "progress": 100, "tags": [tag_pedagogy],
                "lat": 32.4834, "lng": 3.6674, "loc_name": "مكتب التسجيلات وشؤون الطلبة - مجمع نوميرات، غرداية",
                "sub_status": "approved", "score": 95, "sub_date": datetime(2026, 10, 21, 11, 0),
                "sub_notes": "تم الفصل في 142 ملف تحويل بنجاح، وإشعار المعنيين عبر منصة بروغرس الوزارية.",
                "feedback": "تمت المعالجة في الآجال المحددة دون تسجيل أي طعون عالقة."
            },
            {
                "module": "service-inscriptions-orientation",
                "title": "إحصاء وتحديث سجلات الطلبة الأجانب الممنوحين في الكلية للعام الجامعي 2026",
                "desc": "متابعة الوضعية الإدارية والإقامة الأكاديمية لطلبة الدراسات القانونية الوافدين من الدول الإفريقية والعربية.",
                "creator": vd_ped, "assigned": [user_scol],
                "priority": "medium", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 7), "deadline": timezone.make_aware(datetime(2026, 11, 5, 12, 0)),
                "status": "in_progress", "progress": 75, "tags": [tag_pedagogy],
                "lat": 32.4834, "lng": 3.6674, "loc_name": "مكتب شؤون الطلبة والتحويلات - جامعة غرداية",
                "sub_status": "under_review", "score": None, "sub_date": datetime(2026, 10, 23, 15, 0),
                "sub_notes": "تم حصر 28 طالباً أجنبياً وتسليمهم بطاقات الطالب والشهادات المدرسية للموسم الجديد.",
                "feedback": "يرجى التنسيق مع مديرية الخدمات الجامعية لتأمين المنح والإيواء."
            },
            {
                "module": "service-enseignement-evaluation",
                "title": "ضبط رزنامة امتحانات السداسي الأول وتوزيع القاعات والمدرجات",
                "desc": "إعداد الجداول الزمنية المفصلة وتعيين الأساتذة الحراس ولجان تصحيح الامتحانات لجميع الأفواج في قسمي الحقوق والعلوم السياسية.",
                "creator": vd_ped, "assigned": [user_scol, head_law, head_scpo],
                "priority": "critical", "type": "correspondence", "corr_type": "directive", "ref": "ت.ب/ت.ت/2026/45",
                "start": date(2026, 10, 10), "deadline": timezone.make_aware(datetime(2026, 11, 10, 16, 0)),
                "status": "in_progress", "progress": 70, "tags": [tag_pedagogy, tag_exams],
                "lat": 32.4836, "lng": 3.6676, "loc_name": "مكتب لجان الامتحانات - كلية الحقوق، نوميرات، غرداية",
                "sub_status": "submitted", "score": 88, "sub_date": datetime(2026, 10, 27, 9, 30),
                "sub_notes": "المسودة الأولى لرزنامة الامتحانات جاهزة، بانتظار تأكيد رؤساء الأقسام لأفواج الحراسة.",
                "feedback": "تأكيد توزيع القاعات الكبرى وتفادي التداخل في المقاييس المشتركة."
            },
            {
                "module": "service-enseignement-evaluation",
                "title": "متابعة نسبة تقدم الدروس والأعمال الموجهة وإدخال علامات المراقبة المستمرة",
                "desc": "مراسلة الأساتذة لإنهاء رصد علامات التقييم المستمر للطلبة عبر منصة بروغرس الوزارية والتأكد من استكمال الحجم الساعي.",
                "creator": vd_ped, "assigned": [user_scol],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 12), "deadline": timezone.make_aware(datetime(2026, 11, 20, 16, 30)),
                "status": "rejected", "progress": 45, "tags": [tag_pedagogy, tag_exams],
                "lat": 32.4836, "lng": 3.6676, "loc_name": "مصلحة التعليم والتقييم - كلية الحقوق، غرداية",
                "sub_status": "rejected", "score": 55, "sub_date": datetime(2026, 10, 24, 11, 15),
                "sub_notes": "تم استلام قوائم العلامات لـ 60% من الأفواج، ويوجد نقص في أفواج القانون الدولي وقانون الأعمال.",
                "feedback": "مرفوض للاستدراك: يجب إلزام كافة الأساتذة المتأخرين بتقديم محاضر التقييم موقعة خلال 48 ساعة وإعادة الرفع."
            },
            {
                "module": "service-diplomes-parcours",
                "title": "طباعة وتدقيق شهادات الليسانس والماستر ومطابقتها مع السجلات الورقية",
                "desc": "إصدار النسخ النهائية لشهادات النجاح لدفعة جوان 2026 والتحقق من الأرقام التسلسلية والتأشيرات الوزارية.",
                "creator": vd_ped, "assigned": [user_scol],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 3), "deadline": timezone.make_aware(datetime(2026, 10, 30, 15, 0)),
                "status": "completed", "progress": 100, "tags": [tag_pedagogy, tag_admin],
                "lat": 32.4837, "lng": 3.6677, "loc_name": "مكتب تدقيق الشهادات - مجمع نوميرات، غرداية",
                "sub_status": "approved", "score": 97, "sub_date": datetime(2026, 10, 19, 14, 0),
                "sub_notes": "تمت طباعة 320 شهادة ومطابقتها حرفياً مع سجلات المداولات الرسمية، جاهزة للتسليم للطلبة.",
                "feedback": "عمل ممتاز وتدقيق خالٍ من أي أخطاء مادية."
            },
            {
                "module": "dept-droit",
                "title": "توزيع مقاييس السداسي الأول على الأساتذة وتثبيت جداول توقيت المحاضرات",
                "desc": "عقد اجتماع اللجنة البيداغوجية لقسم الحقوق وتوزيع أعباء التدريس لأساتذة القانون العام والخاص وتعيين مسؤولي الفرق.",
                "creator": head_law, "assigned": [user_scol, head_law],
                "priority": "critical", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 1), "deadline": timezone.make_aware(datetime(2026, 10, 27, 16, 0)),
                "status": "completed", "progress": 100, "tags": [tag_pedagogy, tag_legal],
                "lat": 32.4835, "lng": 3.6675, "loc_name": "رئاسة قسم الحقوق - مجمع نوميرات، غرداية",
                "sub_status": "approved", "score": 96, "sub_date": datetime(2026, 10, 18, 12, 0),
                "sub_notes": "تم الانتهاء من إسناد كافة المقاييس لأساتذة القانون العام والخاص بدون أي شغور بيداغوجي.",
                "feedback": "تم اعتماد الجداول وتوزيعها على المدرجات وقاعات التدريس."
            },
            {
                "module": "dept-droit",
                "title": "تنظيم اليوم الدراسي حول 'الضمانات القانونية للمستثمر في التشريع الجزائري الحديث'",
                "desc": "التحضير الأكاديمي واللوجستي لليوم الدراسي بالتعاون مع مخبر الدراسات القانونية وتوجيه الدعوات للهيئات القضائية بغرداية.",
                "creator": head_law, "assigned": [vd_post, user_trib],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 15), "deadline": timezone.make_aware(datetime(2026, 11, 25, 17, 0)),
                "status": "in_progress", "progress": 60, "tags": [tag_research, tag_legal],
                "lat": 32.4835, "lng": 3.6675, "loc_name": "قاعة المحاضرات الكبرى - كلية الحقوق، غرداية",
                "sub_status": "under_review", "score": None, "sub_date": datetime(2026, 10, 26, 10, 30),
                "sub_notes": "تم استلام 18 مداخلة علمية محكمة، وجاري تصميم المطويات الإشهارية وبرنامج الجلسات.",
                "feedback": "موضوع هام ومواكب، يُرجى تأكيد حضور السادة القضاة والمحامين."
            },
            {
                "module": "dept-sciences-politiques",
                "title": "إعداد وتحديث الدليل البيداغوجي لشعبتي العلاقات الدولية والسياسات العامة",
                "desc": "مراجعة برامج التكوين الوزارية، وتحديد المراجع الموصى بها لطلبة الماستر وتوزيع فضاءات التدريس.",
                "creator": head_scpo, "assigned": [user_bib, head_scpo],
                "priority": "medium", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 5), "deadline": timezone.make_aware(datetime(2026, 11, 10, 14, 0)),
                "status": "in_progress", "progress": 75, "tags": [tag_pedagogy],
                "lat": 32.4830, "lng": 3.6670, "loc_name": "رئاسة قسم العلوم السياسية - جامعة غرداية",
                "sub_status": "submitted", "score": 90, "sub_date": datetime(2026, 10, 23, 11, 0),
                "sub_notes": "تم إعداد الدليل بصيغة رقمية PDF مع روابط المراجع المتاحة بمكتبة الكلية.",
                "feedback": "دليل بيداغوجي قيم، يوضع على موقع الكلية الإلكتروني."
            },
            {
                "module": "dept-sciences-politiques",
                "title": "متابعة مشاريع مذكرات التخرج لطلبة الماستر 2 وتوزيع المؤطرين الأكاديميين",
                "desc": "حصر عناوين مذكرات التخرج ومطابقتها مع تخصصات الأساتذة وتثبيت استمارات الإشراف للعام 2026-2027.",
                "creator": head_scpo, "assigned": [head_scpo],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 10), "deadline": timezone.make_aware(datetime(2026, 11, 30, 17, 0)),
                "status": "in_progress", "progress": 80, "tags": [tag_pedagogy, tag_research],
                "lat": 32.4830, "lng": 3.6670, "loc_name": "قسم العلوم السياسية - القطب الجامعي نوميرات، غرداية",
                "sub_status": "submitted", "score": 92, "sub_date": datetime(2026, 10, 27, 14, 0),
                "sub_notes": "تمت المصادقة على 65 موضوع مذكرة تخرج في اللجنة العلمية للقسم وتعيين المشرفين.",
                "feedback": "عمل منظم، يُنشر الجدول لطلبة الماستر 2 للإشعار."
            },

            # Group 3: Scientific Research & External Cooperation
            {
                "module": "service-post-graduation-doctorat",
                "title": "مراجعة ملفات المترشحين لمسابقة الدكتوراه بعنوان السنة الجامعية 2026-2027",
                "desc": "التأكد من استيفاء ملفات طلبة الماستر للشروط القانونية عبر منصة بروغرس وإعداد القوائم الاسمية للمقبولين لاجتياز الاختبارات الكتابية.",
                "creator": vd_post, "assigned": [user_post],
                "priority": "critical", "type": "correspondence", "corr_type": "decision", "ref": "ق.إ/د.ك/2026/12",
                "start": date(2026, 10, 1), "deadline": timezone.make_aware(datetime(2026, 10, 28, 18, 0)),
                "status": "completed", "progress": 100, "tags": [tag_research],
                "lat": 32.4855, "lng": 3.6702, "loc_name": "مصلحة ما بعد التدرج - كلية الحقوق، نوميرات، غرداية",
                "sub_status": "approved", "score": 97, "sub_date": datetime(2026, 10, 22, 16, 45),
                "sub_notes": "تم فحص 310 ملفات للمترشحين في تخصصات القانون العام والقانون الخاص والعلوم السياسية، ونشر النتائج.",
                "feedback": "إنجاز دقيق وفي الآجال المحددة، جاهزون لتنظيم المسابقة الكتابية."
            },
            {
                "module": "service-post-graduation-doctorat",
                "title": "التدقيق في تقارير القابلية لمناقشة أطروحات الدكتوراه الطور الثالث LMD",
                "desc": "التحقق من استيفاء شروط النشر العلمي في المجلات المفهرسة (Catégorie B) ونقاط التكوين المسبق للأطروحات المودعة.",
                "creator": vd_post, "assigned": [user_post],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 6), "deadline": timezone.make_aware(datetime(2026, 11, 15, 15, 0)),
                "status": "in_progress", "progress": 70, "tags": [tag_research],
                "lat": 32.4855, "lng": 3.6702, "loc_name": "مكتب لجان مناقشة الدكتوراه - جامعة غرداية",
                "sub_status": "under_review", "score": None, "sub_date": datetime(2026, 10, 25, 11, 0),
                "sub_notes": "تمت مراجعة 6 ملفات مناقشة وإحالتها على الخبراء المقيمين من جامعات وهران والجزائر 1 وقسنطينة.",
                "feedback": "متابعة التقييمات مع الأساتذة الخبراء للإسراع في منح تراخيص المناقشة."
            },
            {
                "module": "service-recherche-technologies",
                "title": "تقييم الحصيلة السنوية لمشاريع البحث الجامعي التكويني (PRFU) لسنة 2026",
                "desc": "استلام الحصائل السنوية من رؤساء مشاريع PRFU ومطابقة النفقات المنجزة مع المقالات المنشورة في المجلات العلمية.",
                "creator": vd_post, "assigned": [user_post],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 4), "deadline": timezone.make_aware(datetime(2026, 11, 20, 16, 0)),
                "status": "in_progress", "progress": 75, "tags": [tag_research],
                "lat": 32.4858, "lng": 3.6705, "loc_name": "مكتب مشاريع البحث التكويني PRFU - غرداية",
                "sub_status": "submitted", "score": 93, "sub_date": datetime(2026, 10, 24, 15, 30),
                "sub_notes": "تم جمع 14 تقريراً لمشاريع البحث المعتمدة وإعداد ملخص للإرسال إلى الندوة الجهوية للجامعات (CRUO).",
                "feedback": "مؤشرات ممتازة في عدد المنشورات العلمية لأساتذة الكلية."
            },
            {
                "module": "service-cooperation-relations-ext",
                "title": "تجديد اتفاقية الشراكة والتدريب الميداني مع مجلس قضاء غرداية ونقابة المحامين",
                "desc": "صياغة بنود الاتفاقية الإطارية لتأطير تربصات طلبة الحقوق والماستر في المحاكم ومكاتب الموثقين والمحضرين القضائيين.",
                "creator": dean, "assigned": [vd_post, user_trib],
                "priority": "high", "type": "correspondence", "corr_type": "decision", "ref": "ا.ش/ع.خ/2026/05",
                "start": date(2026, 10, 8), "deadline": timezone.make_aware(datetime(2026, 11, 12, 12, 0)),
                "status": "completed", "progress": 100, "tags": [tag_research, tag_legal],
                "lat": 32.4850, "lng": 3.6695, "loc_name": "مكتب العلاقات الخارجية - كلية الحقوق، غرداية",
                "sub_status": "approved", "score": 98, "sub_date": datetime(2026, 10, 26, 10, 0),
                "sub_notes": "تمت مراجعة البنود القانونية للاتفاقية وتحديد موعد حفل التوقيع الرسمي بمجلس قضاء غرداية.",
                "feedback": "إنجاز استراتيجي سيعزز التكوين الميداني لطلبة الكلية بشكل ملحوظ."
            },
            {
                "module": "conseil-scientifique-faculte",
                "title": "دراسة ملفات التأهيل الجامعي للأساتذة الباحثين في القانون والعلوم السياسية",
                "desc": "عقد دورة المجلس العلمي لدراسة تقارير المقرّرين وملفات الترقية إلى رتبة أستاذ محاضر 'أ' والبت في قابلية المناقشة.",
                "creator": vd_post, "assigned": [vd_post],
                "priority": "critical", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 10), "deadline": timezone.make_aware(datetime(2026, 10, 31, 17, 30)),
                "status": "in_progress", "progress": 85, "tags": [tag_research],
                "lat": 32.4846, "lng": 3.6686, "loc_name": "قاعة اجتماعات المجلس العلمي - كلية الحقوق، غرداية",
                "sub_status": "submitted", "score": 94, "sub_date": datetime(2026, 10, 25, 17, 0),
                "sub_notes": "تمت معالجة 4 ملفات تأهيل جامعي، وتم تحرير محاضر التقييم تمهيداً لرفعها لرئاسة الجامعة.",
                "feedback": "عمل دقيق ومحكم وفق المعايير الوزارية."
            },
            {
                "module": "laboratoires-unites-recherche",
                "title": "إعداد ملف تجديد وتوطين فرق البحث بمخبر الدراسات القانونية والقضائية",
                "desc": "حصر الإنتاج العلمي السنوي وتحديث تركيبة الفرق البحثية بالمخبر وإعداد ميزانية الدعم المالي للأجهزة والمراجع.",
                "creator": vd_post, "assigned": [user_post],
                "priority": "medium", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 2), "deadline": timezone.make_aware(datetime(2026, 11, 28, 16, 0)),
                "status": "rejected", "progress": 50, "tags": [tag_research],
                "lat": 32.4862, "lng": 3.6710, "loc_name": "مخبر الدراسات القانونية والقضائية - جامعة غرداية",
                "sub_status": "rejected", "score": 58, "sub_date": datetime(2026, 10, 21, 14, 0),
                "sub_notes": "تم إعداد مسودة تقرير فرق البحث، ولكن بعض الفرق لم تقدم مخرجات النشر العلمي في المجلات المفهرسة.",
                "feedback": "مرفوض للاستدراك: يلزم إلزام مديري الفرق بتوثيق الروابط المفهرسة للمقالات وإعادة إرسال الملف كاملاً."
            },

            # Group 4: Administrative & Technical Support
            {
                "module": "service-personnel-rh",
                "title": "إعداد المخطط السنوي لتسيير الموارد البشرية والترقيات المهنية لسنة 2026",
                "desc": "حصر جداول الترقية على أساس الشهادة والاختبار المهني وتحديث الوضعيات الإدارية لموظفي الأسلاك المشتركة والأساتذة.",
                "creator": sg, "assigned": [user_rh],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 1), "deadline": timezone.make_aware(datetime(2026, 10, 30, 16, 0)),
                "status": "completed", "progress": 100, "tags": [tag_admin],
                "lat": 32.4841, "lng": 3.6681, "loc_name": "مصلحة الموظفين والموارد البشرية - كلية الحقوق، غرداية",
                "sub_status": "approved", "score": 96, "sub_date": datetime(2026, 10, 20, 11, 30),
                "sub_notes": "تم إعداد المخطط السنوي ومصادقته من المراقب المالي ومفتشية الوظيفة العمومية لولاية غرداية.",
                "feedback": "إنجاز ممتاز ومطابق لتعليمات المديرية العامة للوظيفة العمومية."
            },
            {
                "module": "service-personnel-rh",
                "title": "متابعة سجلات الحضور والانضباط الإداري والشهادات الطبية للموظفين والأساتذة",
                "desc": "تدقيق سجلات التوقيع اليومية والتقارير الشهرية للغيابات والإجازات القانونية وإعداد قرارات الخصم عند الاقتضاء.",
                "creator": sg, "assigned": [user_rh],
                "priority": "medium", "type": "correspondence", "corr_type": "circular", "ref": "م.ع/م.ب/2026/89",
                "start": date(2026, 10, 5), "deadline": timezone.make_aware(datetime(2026, 11, 5, 12, 0)),
                "status": "in_progress", "progress": 80, "tags": [tag_admin],
                "lat": 32.4841, "lng": 3.6681, "loc_name": "مكتب تسيير المستخدمين - الجناح الإداري، نوميرات، غرداية",
                "sub_status": "submitted", "score": 91, "sub_date": datetime(2026, 10, 26, 15, 0),
                "sub_notes": "تم تسجيل انضباط عالٍ بنسبة حضور 96% لكافة مصالح الكلية خلال شهر أكتوبر.",
                "feedback": "متابعة جيدة، واصلوا تطبيق النظام الداخلي بحزم."
            },
            {
                "module": "service-budget-finances",
                "title": "إعداد الكشوف المالية لصرف الساعات الإضافية ومستحقات التأطير للسداسي السابق",
                "desc": "مراجعة كشوف التدريس للساعات الإضافية المعتمدة من رؤساء الأقسام وإعداد بطاقات الالتزام المالي والمحاسبي.",
                "creator": sg, "assigned": [user_fin],
                "priority": "critical", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 3), "deadline": timezone.make_aware(datetime(2026, 10, 29, 15, 0)),
                "status": "completed", "progress": 100, "tags": [tag_budget],
                "lat": 32.4842, "lng": 3.6682, "loc_name": "مصلحة المحاسبة والمالية - مجمع نوميرات، غرداية",
                "sub_status": "approved", "score": 97, "sub_date": datetime(2026, 10, 21, 16, 0),
                "sub_notes": "تم إيداع الحوالات لدى المراقب المالي وأمين الخزينة الرئيسي بولاية غرداية بنجاح.",
                "feedback": "عمل مالي منظم سيضمن تسليم المستحقات للأساتذة في أقرب الآجال."
            },
            {
                "module": "service-budget-finances",
                "title": "مشروع الميزانية التقديرية الأولية للكلية بعنوان السنة المالية 2027",
                "desc": "جمع الاحتياجات التقديرية لمختلف المصالح والأقسام والمخابر وصياغة مشروع ميزانية التسيير والتجهيز لسنة 2027.",
                "creator": sg, "assigned": [user_fin],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 10), "deadline": timezone.make_aware(datetime(2026, 11, 25, 17, 0)),
                "status": "in_progress", "progress": 65, "tags": [tag_budget],
                "lat": 32.4842, "lng": 3.6682, "loc_name": "مكتب الميزانية التقديرية - جامعة غرداية",
                "sub_status": "under_review", "score": None, "sub_date": datetime(2026, 10, 25, 14, 0),
                "sub_notes": "تم استلام المقترحات الأولية وتصنيفها حسب الأبواب والبنود المحاسبية القانونية.",
                "feedback": "التركيز على تدعيم ميزانية مخابر البحث وقاعة المحاكمات الافتراضية."
            },
            {
                "module": "service-moyens-generaux-maintenance",
                "title": "صيانة وتهيئة أجهزة التكييف والإنارة بقاعات التدريس والمدرجات الكبرى",
                "desc": "إجراء الصيانة الدورية لمنظومة التبريد والتكييف والكهرباء بالمدرج 'أ' والمدرج 'ب' وقاعات المحاضرات.",
                "creator": sg, "assigned": [user_rh],
                "priority": "medium", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 5), "deadline": timezone.make_aware(datetime(2026, 10, 28, 16, 0)),
                "status": "completed", "progress": 100, "tags": [tag_admin],
                "lat": 32.4858, "lng": 3.6715, "loc_name": "مجمع المدرجات الكبرى - كلية الحقوق، نوميرات، غرداية",
                "sub_status": "approved", "score": 93, "sub_date": datetime(2026, 10, 22, 10, 30),
                "sub_notes": "تم تغيير المصابيح التالفة وفحص أجهزة التكييف والتأكد من جاهزيتها الكاملة.",
                "feedback": "شكراً لجهود فريق الصيانة في تحسين ظروف التدريس للطلبة والأساتذة."
            },
            {
                "module": "service-informatique-statistiques",
                "title": "تحديث البنية التحتية للشبكة اللاسلكية (Wi-Fi) وتأمين خوادم الكلية المحلية",
                "desc": "تثبيت نقاط وصول جديدة في المكتبة وقاعة الأساتذة وربطها بنظام الأمان والمصادقة المركزي (Radius Server).",
                "creator": sg, "assigned": [user_it],
                "priority": "critical", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 2), "deadline": timezone.make_aware(datetime(2026, 10, 27, 18, 0)),
                "status": "completed", "progress": 100, "tags": [tag_digit],
                "lat": 32.4848, "lng": 3.6688, "loc_name": "مركز البيانات والشبكات - كلية الحقوق، نوميرات، غرداية",
                "sub_status": "approved", "score": 99, "sub_date": datetime(2026, 10, 19, 16, 30),
                "sub_notes": "تم تركيب 12 نقطة اتصال Cisco جديدة واختبار سرعة النطاق الترددي واستقرار الشبكة.",
                "feedback": "عمل تقني احترافي عالي المستوى يضمن تجربة رقمية ممتازة للأساتذة والطلبة."
            },
            {
                "module": "service-informatique-statistiques",
                "title": "إعداد الإحصاء الرقمي الشامل لطلبة وأساتذة الكلية ورفعه للبوابة المركزية",
                "desc": "استخراج الإحصائيات الدقيقة لطلبة الليسانس والماستر والدكتوراه وتصنيفها حسب الجنس والتخصص ورفعها للوزارة الوصية.",
                "creator": sg, "assigned": [user_it, user_scol],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 8), "deadline": timezone.make_aware(datetime(2026, 11, 5, 15, 0)),
                "status": "in_progress", "progress": 85, "tags": [tag_digit, tag_admin],
                "lat": 32.4848, "lng": 3.6688, "loc_name": "مصلحة الإحصاء والرقمنة - جامعة غرداية",
                "sub_status": "submitted", "score": 94, "sub_date": datetime(2026, 10, 26, 11, 0),
                "sub_notes": "التقرير الإحصائي مكتمل بنسبة 95%، تم التحقق من أرقام التسجيل مطابقة لنظام بروغرس.",
                "feedback": "عمل دقيق سيعتمد في التقرير السنوي للجامعة."
            },

            # Group 5: Facilities & Auxiliary Scientific Services
            {
                "module": "bibliotheque-faculte-archives",
                "title": "فهرسة الكتب والمراجع القانونية الجديدة ورقمنة مذكرات الماستر المودعة حديثاً",
                "desc": "إدخال المقتنيات الحديثة إلى النظام الآلي للمكتبة (Koha)، وإتاحة النسخ الرقمية للأساتذة والباحثين عبر السيرفر المحلي.",
                "creator": sg, "assigned": [user_bib],
                "priority": "medium", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 3), "deadline": timezone.make_aware(datetime(2026, 10, 30, 16, 0)),
                "status": "in_progress", "progress": 80, "tags": [tag_digit, tag_pedagogy],
                "lat": 32.4851, "lng": 3.6690, "loc_name": "المكتبة المركزية - قاعة المطالعة، نوميرات، غرداية",
                "sub_status": "submitted", "score": 91, "sub_date": datetime(2026, 10, 25, 12, 0),
                "sub_notes": "تمت معالجة وفهرسة 230 مرجعاً جديداً في القانون العام والخاص والعلوم السياسية، ورقمنة 85 مذكرة ماستر.",
                "feedback": "مجهود معتبر في إثراء الرصيد البيبليوغرافي لمكتبة الكلية."
            },
            {
                "module": "bibliotheque-faculte-archives",
                "title": "تنظيم معرض الكتاب القانوني السنوي وتوسيع الاشتراكات في قواعد البيانات العالمية",
                "desc": "التنسيق مع دور النشر الجامعية ومكتبات الحقوق الوطنية لإقامة صالون الكتاب وتوفير المراجع المتخصصة للطلبة.",
                "creator": sg, "assigned": [user_bib],
                "priority": "low", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 10), "deadline": timezone.make_aware(datetime(2026, 11, 20, 14, 0)),
                "status": "in_progress", "progress": 60, "tags": [tag_pedagogy],
                "lat": 32.4851, "lng": 3.6690, "loc_name": "رواق المعارض بمكتبة كلية الحقوق - غرداية",
                "sub_status": "under_review", "score": None, "sub_date": datetime(2026, 10, 24, 16, 0),
                "sub_notes": "تم الاتصال بـ 5 دور نشر أكاديمية وتأكيد مشاركتهم في فعاليات الصالون في نوفمبر القادم.",
                "feedback": "مبادرة هادفة لتشجيع القراءة والبحث العلمي لطلبة الكلية."
            },
            {
                "module": "tribunal-virtuel-moot-court",
                "title": "تنظيم جلسة المحاكمة الصورية الأولى في القانون الجنائي والإجراءات الجزائية",
                "desc": "تجهيز قاعة المحاكمات الافتراضية، وتوزيع أدوار القضاة والدفاع والنيابة العامة على طلبة الماستر تحت إشراف محامين وقضاة ممارسين.",
                "creator": dean, "assigned": [user_trib, head_law],
                "priority": "critical", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 2), "deadline": timezone.make_aware(datetime(2026, 10, 29, 17, 0)),
                "status": "completed", "progress": 100, "tags": [tag_legal, tag_pedagogy],
                "lat": 32.4839, "lng": 3.6678, "loc_name": "قاعة المحاكمات الافتراضية - مجمع نوميرات، غرداية",
                "sub_status": "approved", "score": 98, "sub_date": datetime(2026, 10, 23, 17, 30),
                "sub_notes": "تم إجراء المحاكمة الصورية بنجاح مبهر وبحضور السيد رئيس مجلس قضاء غرداية ونقيب المحامين.",
                "feedback": "تجربة بيداغوجية نموذجية تركت أثراً تدريبياً استثنائياً لدى طلبة الكلية."
            },
            {
                "module": "tribunal-virtuel-moot-court",
                "title": "برمجة ورشات المرافعة الشفوية وصياغة العرائض القضائية للعام 2026",
                "desc": "وضع جدول زمني للورشات التطبيقية الأسبوعية لتدريب طلبة الكلية على تقنيات الإقناع الشفوي وصياغة المذكرات القانونية.",
                "creator": head_law, "assigned": [user_trib],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 10), "deadline": timezone.make_aware(datetime(2026, 11, 20, 15, 0)),
                "status": "in_progress", "progress": 70, "tags": [tag_legal],
                "lat": 32.4839, "lng": 3.6678, "loc_name": "قاعة المحاكمة الصورية - كلية الحقوق، غرداية",
                "sub_status": "submitted", "score": 92, "sub_date": datetime(2026, 10, 27, 10, 0),
                "sub_notes": "تم تسجيل 45 طالباً في الورشات وتعيين 4 أساتذة محامين للتأطير التطبيقي.",
                "feedback": "برنامج رائع، يُعتمد وينطلق العمل به ابتداءً من الأسبوع القادم."
            },
            {
                "module": "clubs-associations-scientifiques",
                "title": "تنظيم المسابقة الجامعية للمناظرات القانونية والفكرية بين طلبة الكلية",
                "desc": "إشراف النادي العلمي للحقوق على تصفيات المناظرة في قضايا الحريات العامة والتحول الرقمي للعدالة في الجزائر.",
                "creator": vd_ped, "assigned": [user_trib],
                "priority": "medium", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 5), "deadline": timezone.make_aware(datetime(2026, 10, 28, 17, 0)),
                "status": "completed", "progress": 100, "tags": [tag_legal, tag_pedagogy],
                "lat": 32.4828, "lng": 3.6660, "loc_name": "فضاء الأنشطة الطلابية والنوادي - جامعة غرداية",
                "sub_status": "approved", "score": 95, "sub_date": datetime(2026, 10, 20, 18, 0),
                "sub_notes": "شاركت 8 فرق طلابية في التصفيات، وتم تتويج الفريق الفائز بحضور أساتذة الكلية.",
                "feedback": "نشاط طلابي متميز يعزز الملكة الخطابية والقدرة على المحاجة القانونية."
            },
            {
                "module": "clubs-associations-scientifiques",
                "title": "إطلاق مبادرة 'العيادة القانونية الاستشارية' التطوعية لخدمة المجتمع المحلي بغرداية",
                "desc": "تأطير نادي الحقوق لتقديم استشارات قانونية مبسطة وتوعية المواطنين بحقوقهم بالتنسيق مع أساتذة الكلية ومحامي الولاية.",
                "creator": vd_ped, "assigned": [user_trib],
                "priority": "high", "type": "standard", "corr_type": None, "ref": "",
                "start": date(2026, 10, 12), "deadline": timezone.make_aware(datetime(2026, 11, 30, 18, 0)),
                "status": "rejected", "progress": 40, "tags": [tag_legal],
                "lat": 32.4828, "lng": 3.6660, "loc_name": "مقر النوادي العلمية - القطب الجامعي نوميرات، غرداية",
                "sub_status": "rejected", "score": 50, "sub_date": datetime(2026, 10, 23, 16, 0),
                "sub_notes": "تم تقديم مشروع المبادرة لكن ينقصه التصريح الأمني ومصادقة عمادة الكلية ونقابة المحامين.",
                "feedback": "مرفوض للاستدراك: يجب أولاً الحصول على التراخيص الإدارية اللازمة وصياغة ميثاق أخلاقيات العيادة قبل الإطلاق."
            },
        ]

        created_tasks_list = []
        for t_spec in tasks_raw_data:
            mod = created_modules.get(t_spec["module"])
            if not mod:
                continue

            task = Task.objects.create(
                work_module=mod,
                title=t_spec["title"],
                description=t_spec["desc"],
                created_by=t_spec["creator"],
                start_date=t_spec["start"],
                deadline=t_spec["deadline"],
                priority=t_spec["priority"],
                task_type=t_spec["type"],
                correspondence_type=t_spec.get("corr_type"),
                reference_number=t_spec.get("ref", ""),
                estimated_hours=14.0,
                kpi_weight=1.5,
                status=t_spec["status"],
                progress=t_spec["progress"],
                cover_image=DEFAULT_COVER_PATH,
                location_enabled=True,
                latitude=t_spec["lat"],
                longitude=t_spec["lng"],
                location_name=t_spec["loc_name"],
                country="الجزائر",
                wilaya="غرداية",
            )
            for asg_user in t_spec["assigned"]:
                task.assigned_to.add(asg_user)
            for tg in t_spec.get("tags", []):
                task.tags.add(tg)

            created_tasks_list.append(task)

            # Sync with dedicated Correspondence model if correspondence type
            if task.task_type == "correspondence":
                from tasks.models import Correspondence, CorrespondenceAcknowledgement
                corr, _ = Correspondence.objects.get_or_create(
                    title=task.title,
                    defaults={
                        "description": task.description,
                        "correspondence_type": task.correspondence_type or "memo",
                        "reference_number": task.reference_number,
                        "priority": task.priority,
                        "deadline": task.deadline,
                        "work_module": task.work_module,
                        "created_by": task.created_by,
                        "cover_image": task.cover_image,
                        "status": "active",
                    }
                )
                for asg in task.assigned_to.all():
                    corr.assigned_to.add(asg)
                    if t_spec.get("sub_status") == "approved":
                        CorrespondenceAcknowledgement.objects.get_or_create(
                            correspondence=corr,
                            user=asg,
                            defaults={"note": "تم الاطلاع والمصادقة الإدارية"}
                        )

            # Create associated Submissions in October 2026
            primary_worker = t_spec["assigned"][0]
            sub_dt = timezone.make_aware(t_spec["sub_date"])
            rev_dt = sub_dt + timedelta(hours=4) if t_spec["sub_status"] in ["approved", "rejected"] else None

            sub = Submission.objects.create(
                task=task,
                worker=primary_worker,
                reviewed_by=t_spec["creator"] if t_spec["sub_status"] in ["approved", "rejected"] else None,
                notes=t_spec["sub_notes"],
                manager_feedback=t_spec.get("feedback", ""),
                score=t_spec.get("score"),
                status=t_spec["sub_status"],
                progress=100 if t_spec["sub_status"] == "approved" else (50 if t_spec["sub_status"] == "rejected" else 75),
                submitted_at=sub_dt,
                reviewed_at=rev_dt,
                version=1,
            )

            # Attach feedback comment if available
            if t_spec.get("feedback"):
                SubmissionComment.objects.create(
                    submission=sub,
                    author=t_spec["creator"],
                    comment=t_spec["feedback"],
                    action_type="approval" if t_spec["sub_status"] == "approved" else ("review_request" if t_spec["sub_status"] == "rejected" else "comment"),
                    progress=sub.progress,
                )

            # Create Notification for assigned users
            for asg in t_spec["assigned"]:
                Notification.objects.create(
                    recipient=asg,
                    notification_type="task_assigned",
                    title=f"مهمة جديدة: {task.title[:50]}...",
                    message=f"تم إسناد مهمة جديدة لك في وحدة '{mod.name}' ضمن هيكل كلية الحقوق والعلوم السياسية.",
                    related_object_type="task",
                    related_object_id=task.id,
                    is_read=random.choice([True, False]),
                )

            # If rejected, create a specific notification so workers can track
            if t_spec["sub_status"] == "rejected":
                Notification.objects.create(
                    recipient=primary_worker,
                    notification_type="submission_rejected",
                    title=f"استدراك مطلوب: {task.title[:50]}...",
                    message=f"تم طلب استدراك على تسليم المهمة: '{t_spec.get('feedback')}'",
                    related_object_type="submission",
                    related_object_id=sub.id,
                    is_read=False,
                )
            elif t_spec["sub_status"] == "approved":
                Notification.objects.create(
                    recipient=primary_worker,
                    notification_type="submission_approved",
                    title=f"تم اعتماد التسليم: {task.title[:50]}...",
                    message=f"تمت المصادقة على تسليم المهمة بنقطة تقييم {t_spec.get('score')}/100.",
                    related_object_type="submission",
                    related_object_id=sub.id,
                    is_read=True,
                )

        # D. Peer-to-Peer Academic Messaging System
        # Requirement: between each users should have messages 10 message go and back at least with 7 other users
        n_staff = len(all_staff_list)
        # Pre-scripted academic conversation dialog templates for authentic exchanges
        academic_dialog_pairs = [
            # Topic 1: Exam and Pedagogical Follow-up
            [
                ("السلام عليكم ورحمة الله، كيف تسير التحضيرات لرزنامة امتحانات السداسي الأول؟", "وعليكم السلام ورحمة الله أستاذنا، قمنا بضبط جداول الحراسة للمدرجات 'أ' و 'ب' بنسبة 95%."),
                ("ممتاز، هل تم التنسيق مع مصلحة الصيانة لتفقد أجهزة التدفئة والصوتيات؟", "نعم تم ذلك بالفعل، ومصلحة الوسائل العامة أتمت معاينة المدرجات وجميعها جاهزة."),
                ("أرجو التأكيد على الأساتذة لإنهاء رصد نقاط المراقبة المستمرة قبل يوم الخميس.", "تم إرسال تنبيه إداري عبر البريد الوزاري لكافة الزملاء الأساتذة في القسم."),
                ("هل توجد أي استفسارات أو طعون من الطلبة بخصوص التحويلات الجامعية؟", "لا توجد طعون معلقة، مصلحة التسجيلات حسمت كافة الملفات بدقة عالية."),
                ("بارك الله في جهودكم، سنعرض الحصيلة الكاملة في مجلس الكلية القادم.", "شكراً جزيلاً سيدي العميد، بالتوفيق للجميع ودمتم ذخراً للكلية.")
            ],
            # Topic 2: Research & Doctoral Contests
            [
                ("تحية طيبة زميلي الكريم، بخصوص ملفات مسابقة الدكتوراه الطور الثالث، هل انتهى الفحص؟", "أهلاً وسهلاً دكتور، نعم تم فحص كافة الملفات المودعة عبر منصة بروغرس."),
                ("كم بلغ العدد النهائي للمقبولين لاجتياز الاختبارات الكتابية؟", "تم قبول 310 مترشحاً في شعبتي القانون العام والخاص والعلوم السياسية."),
                ("ممتاز، وماذا عن لجان صياغة مواضيع الاختبارات وطباعتها في ظروف سرية؟", "اللجان العلمية تم تنصيبها بإشراف المجلس العلمي والظروف مهيأة بالكامل."),
                ("هل تم استلام ميزانية دعم مشاريع البحث التكويني PRFU من رئاسة الجامعة؟", "نعم، أودعنا الكشوف المالية لدى مصلحة الميزانية وسيتم الصرف هذا الأسبوع."),
                ("وفقكم الله، سنلتقي غداً صباحاً لمراجعة المخطط النهائي قبل النشر.", "على بركة الله دكتور، نلتقي بمكتب ما بعد التدرج إن شاء الله.")
            ],
            # Topic 3: Virtual Moot Court & Training
            [
                ("السلام عليكم أستاذ مصطفى، كيف كان صدى جلسة المحاكمة الصورية الأولى؟", "وعليكم السلام دكتور بشير، الأصداء كانت استثنائية من السادة القضاة والطلبة."),
                ("حضور السيد رئيس مجلس قضاء غرداية ونقيب المحامين أعطى الجلسة وزناً كبيراً.", "بالتأكيد، وقد أشادوا بمستوى مرافعة طلبة الماستر 2 ودقة أدائهم الإجرائي."),
                ("هل بدأتم التحضير لورشة صياغة العرائض والاستشارات القانونية القادمة؟", "نعم سجلنا 45 طالباً، وأستاذان من المحامين الممارسين تطوعوا للتأطير."),
                ("سنقوم بتخصيص ميزانية إضافية من الأمانة العامة لتزويد القاعة بنظام تسجيل رقمي.", "هذا دعم رائع سيسمح للطلبة بمراجعة تسجيلات مرافعاتهم وتطوير ملكاتهم."),
                ("هذا واجبنا تجاه طلبتنا، نتمنى استمرار هذا التميز والتألق.", "جزاكم الله كل خير، دائماً في خدمة كليتنا وجامعة غرداية.")
            ],
            # Topic 4: Budget, Procurement & Maintenance
            [
                ("مرحباً أستاذ عمر، كيف هو وضع الالتزامات المالية للثلاثي الأخير من السنة؟", "مرحباً سيدي الأمين العام، تمكنا من تسديد 85% من الفواتير ومستحقات الأساتذة."),
                ("هل تمت معالجة كشوف الساعات الإضافية للأساتذة المؤقتين؟", "نعم، الحوالات مودعة حالياً لدى خزينة ولاية غرداية والصرف وشيك."),
                ("أرجو التأكد من حجز اعتمادات الصيانة الشتوية ومستلزمات التدريس والمكاتب.", "الاعتمادات محجوزة ومؤشرة من المراقب المالي دون أي ملاحظات."),
                ("بالنسبة لقاعة الإعلام الآلي والمكتبة، هل تم توفير الأحبار والورق اللازم؟", "تم التوزيع صباح اليوم لمصلحة الرقمنة وأمانة المكتبة بالكامل."),
                ("جهود مشكورة ومقدرة، حافظوا على هذا الانضباط المالي المحكم.", "شكراً لثقتكم وتوجيهاتكم المستمرة سيدي الأمين العام.")
            ],
            # Topic 5: IT Infrastructure & Digital Platform
            [
                ("السلام عليكم مهندس إلياس، كيف هي استقرار الشبكة والإنترنت في الكلية؟", "وعليكم السلام دكتور، قمنا بتثبيت 12 نقطة واي فاي جديدة وسرعة التدفق ممتازة."),
                ("هل تم ربط منصة الكلية بمخدمات بروغرس الوزارية دون انقطاع؟", "الربط مستقر بنسبة 99.9%، وقمنا بإنشاء نسخة احتياطية يومية لقواعد البيانات."),
                ("رؤساء الأقسام بحاجة لتقارير إحصائية دورية عن رصد علامات الطلبة.", "لوحة القيادة البرمجية جاهزة ويمكنهم تحميل تقارير PDF وإكسل بضغطة زر."),
                ("ماذا عن قاعات المطالعة الرقمية بالمكتبة المركزية؟", "أجهزة الحواسيب البالغ عددها 30 جهازاً تم تحديث برامجها وربطها بنظام Koha."),
                ("عمل تكنولوجي رائد يواكب رؤية الوزارة في الرقمنة الشاملة.", "نحن في الخدمة دائماً لدعم كافة المصالح والأساتذة تقنياً.")
            ],
            # Topic 6: Library, Documentation & Thesis Archives
            [
                ("تحياتي أستاذة ليلى، كم بلغ عدد مذكرات الماستر المودعة والمفهرسة؟", "تحياتي دكتور، قمنا بفهرسة 85 مذكرة ماستر لسنة 2026 ورفع نسخها الرقمية."),
                ("هل قاعات المطالعة تشهد إقبالاً منتظماً من طلبة الدكتوراه والباحثين؟", "الإقبال كثيف جداً خاصة في الفترة الصباحية، والطلبة يشيدون بتوفر المراجع الحديثة."),
                ("هل نحتاج لطلب مراجع إضافية في القانون الإداري والتحكيم التجاري الدولي؟", "نعم أعددنا قائمة بـ 60 كتاباً حديثاً لعرضها في صالون الكتاب القادم."),
                ("سنرفع الطلب للأمانة العامة لاعتماد شرائها وتزويد المكتبة بها.", "شكراً لاهتمامكم الدائم بتطوير الرصيد العلمي لمكتبة الكلية."),
                ("المكتبة هي القلب النابض للكلية، ونسعى دائماً لدعمكم وتوفير احتياجاتكم.", "بارك الله فيكم ووفقكم لكل خير.")
            ],
            # Topic 7: Student Clubs, Scientific Debates & Logistics
            [
                ("السلام عليكم زميلي، كيف تسير الترتيبات لمسابقة المناظرات القانونية الطلابية؟", "وعليكم السلام، الإقبال من الطلبة رائع ولدينا 8 فرق جاهزة للتنافس."),
                ("ما هي المواضيع المختارة للجولة النهائية للمناظرة؟", "تم اختيار موضوع 'المسؤولية المدنية والذكاء الاصطناعي في القانون الجزائري'."),
                ("اختيار متميز ومواكب للنقاشات التشريعية الحديثة، هل تم حجز القاعة؟", "نعم تم حجز قاعة المحاضرات الكبرى وتجهيز الدروع والشهادات التكريمية."),
                ("سنحضر الافتتاح الرسمي مع السيد العميد وأعضاء المجلس العلمي لتشجيعهم.", "حضوركم يشكل حافزاً كبيراً لأبنائنا الطلبة في نواديهم العلمية."),
                ("دمتم شعلة نشاط وعطاء لكليتنا الحبيبة.", "كل الشكر والتقدير لكم دكتورنا الفاضل.")
            ]
        ]

        # Connect every user to at least 7 distinct colleagues
        # Graph generation: User i connects with (i + 1..7) % 14
        total_conv_count = 0
        total_msg_count = 0

        for i, user_a in enumerate(all_staff_list):
            for step in range(1, 8):
                partner_idx = (i + step) % n_staff
                user_b = all_staff_list[partner_idx]

                # Ensure canonical pairing so we create 1 conversation between A and B
                if user_a.id > user_b.id:
                    continue

                conv_name = f"تنسيق أكاديمي: {user_a.last_name} — {user_b.last_name}"
                conv = Conversation.objects.create(
                    name=conv_name,
                    is_group=False,
                    creator=user_a,
                )
                ConversationMember.objects.create(conversation=conv, user=user_a, is_admin=True)
                ConversationMember.objects.create(conversation=conv, user=user_b, is_admin=False)
                total_conv_count += 1

                # Select dialogue template
                dialog_idx = (i + step) % len(academic_dialog_pairs)
                dialog_exchanges = academic_dialog_pairs[dialog_idx]

                # Generate 10 back-and-forth messages (5 from A, 5 from B alternating)
                # Spread timestamps across October 2026
                base_time = timezone.make_aware(datetime(2026, 10, random.randint(15, 27), random.randint(8, 16), random.randint(0, 45)))
                msg_step_min = 6

                for pair_idx, (txt_a, txt_b) in enumerate(dialog_exchanges):
                    # Message from user_a
                    m_a = Message.objects.create(
                        conversation=conv,
                        sender=user_a,
                        content=txt_a,
                    )
                    t_a = base_time + timedelta(minutes=(pair_idx * 2 * msg_step_min))
                    Message.objects.filter(id=m_a.id).update(timestamp=t_a)

                    # Message from user_b
                    m_b = Message.objects.create(
                        conversation=conv,
                        sender=user_b,
                        content=txt_b,
                    )
                    t_b = base_time + timedelta(minutes=((pair_idx * 2 + 1) * msg_step_min))
                    Message.objects.filter(id=m_b.id).update(timestamp=t_b)

                    total_msg_count += 2

        # E. Daily Attendance Records for All Staff Members in October 2026
        for staff_mem in all_staff_list:
            for d_offset in range(1, 6):
                att_date = date(2026, 10, 28) - timedelta(days=d_offset)
                if att_date.weekday() in [4, 5]:  # Skip Friday/Saturday weekend in Algeria
                    continue
                AttendanceRecord.objects.get_or_create(
                    user=staff_mem,
                    date=att_date,
                    defaults={
                        "check_in": "07:55:00",
                        "status": "present",
                        "total_hours": 7.5,
                        "notes": "دوام رسمي منتظم - كلية الحقوق والعلوم السياسية",
                    }
                )

        return {
            "success": True,
            "status": "success",
            "mode": "faculty_seeded",
            "super_admin": super_admin.email,
            "groups_count": len(FACULTY_GROUPS),
            "modules_count": len(created_modules) + 1,
            "users_count": len(created_users) + 1,
            "tasks_count": len(created_tasks_list),
            "conversations_count": total_conv_count,
            "messages_count": total_msg_count,
            "message": "تمت بنجاح كامل تهيئة كافة المجموعات، الوحدات باللافتات الافتراضية، المهام في غرداية، التسليمات في أكتوبر 2026، والمحادثات المتبادلة بين الكوادر."
        }
