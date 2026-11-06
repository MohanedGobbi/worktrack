"""
Script de seed : crée 5 utilisateurs réalistes + 5 tâches par unité
dans le module 'قسم الإعلام والاتصال التربوي' (+ ses sous-unités),
chaque tâche est assignée, avec une soumission de travail.
"""
import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "worktrack_pro.settings")
django.setup()

from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta, date
import random

from users.models import CustomUser, Department
from tasks.models import Task, TaskComment
from submissions.models import Submission, SubmissionComment
from work_modules.models import WorkModule

# ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
# 1.  FIND THE MEDIA/COMMUNICATION MODULES
# ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
COMM_SLUGS = [
    'mod-c0c85b22',   # قسم الإعلام والاتصال التربوي
    'mod-3e7e10e1',   # مصلحة النشر والتوزيع
    'mod-a6d2055c',   # مصلحة العلاقات العامة والتوثيق
]
modules = list(WorkModule.objects.filter(slug__in=COMM_SLUGS))
if not modules:
    print("Warning: no comm modules found, using first 3")
    modules = list(WorkModule.objects.all()[:3])

# ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
# 2.  CREATE 5 USERS
# ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
dept = Department.objects.first()
admin = CustomUser.objects.filter(role='super_admin').first()

USERS_DATA = [
    dict(username='n.boudiaf', first_name='نادية',  last_name='بوضياف',
         email='n.boudiaf@cndp.dz',     role='manager'),
    dict(username='k.ferhat',  first_name='كريم',   last_name='فرحات',
         email='k.ferhat@cndp.dz',      role='worker'),
    dict(username='s.amrani',  first_name='سلمى',   last_name='عمراني',
         email='s.amrani@cndp.dz',      role='worker'),
    dict(username='m.oukaci',  first_name='مصطفى',  last_name='أوكاسي',
         email='m.oukaci@cndp.dz',      role='worker'),
    dict(username='h.belarbi', first_name='حياة',   last_name='بلعربي',
         email='h.belarbi@cndp.dz',     role='worker'),
]

created_users = []
for ud in USERS_DATA:
    user, created = CustomUser.objects.get_or_create(
        username=ud['username'],
        defaults={
            'email':       ud['email'],
            'first_name':  ud['first_name'],
            'last_name':   ud['last_name'],
            'role':        ud['role'],
            'department':  dept,
            'is_active':   True,
            'admin_owner': admin,
        }
    )
    if created:
        user.set_password('Cndp@2025!')
        user.save()
        print(f"Created user: {user.username}")
    else:
        print(f"User exists: {user.username}")
    created_users.append(user)

manager_user = created_users[0]
workers      = created_users[1:]

# ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
# 3.  TASKS PER MODULE
# ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
TASK_SCENARIOS = {
    'mod-c0c85b22': [
        dict(
            title='إعداد النشرة الإخبارية التربوية – أكتوبر 2025',
            description='إعداد وتحرير النشرة الإخبارية الشهرية للمركز الوطني للوثائق التربوية لشهر أكتوبر 2025، تشمل أبرز الفعاليات التربوية، الإحصاءات الجديدة، والمستجدات في مجال التوثيق التربوي الوطني. يجب أن تكون النشرة جاهزة للنشر في الموقع الرسمي وعلى وسائل التواصل الاجتماعي.',
            priority='high', status='in_progress', progress=60,
            deadline_days=10,
            assignees=[0, 1],
            sub_note='تم إعداد مسودة النشرة الأولى وإرفاقها، بانتظار المراجعة والموافقة.',
        ),
        dict(
            title='تصميم البوسترات التوعوية لأسبوع القراءة الوطني',
            description='تصميم مجموعة من البوسترات التوعوية للترويج لأسبوع القراءة الوطني 2025، تشمل 6 بوسترات بأحجام مختلفة (A3، A4، منشور رقمي)، مع الالتزام بالهوية البصرية للمركز وتوجيهات الدليل البصري.',
            priority='medium', status='submitted', progress=100,
            deadline_days=5,
            assignees=[2],
            sub_note='تم إنجاز جميع البوسترات المطلوبة (6 بوسترات) ورفعها للمراجعة.',
        ),
        dict(
            title='تحديث صفحة الإعلام على الموقع الرسمي للمركز',
            description='مراجعة وتحديث محتوى صفحة الإعلام والاتصال على الموقع الرسمي للمركز، تشمل: إضافة الأخبار الجديدة، تحديث قائمة الإصدارات، تحسين تجربة المستخدم في قسم المستجدات الإعلامية.',
            priority='medium', status='approved', progress=100,
            deadline_days=-2,
            assignees=[3],
            sub_note='تم تحديث الصفحة بالكامل وتم اعتماد المحتوى من طرف المسؤول.',
        ),
        dict(
            title='إعداد تقرير التغطية الإعلامية لملتقى التوثيق التربوي',
            description='إعداد تقرير شامل عن التغطية الإعلامية لملتقى التوثيق التربوي الوطني المنعقد في أكتوبر 2025، يتضمن: تحليل التغطيات الإعلامية في الصحف الوطنية، المواقع الإلكترونية، القنوات التلفزيونية، ووسائل التواصل الاجتماعي.',
            priority='high', status='pending', progress=15,
            deadline_days=20,
            assignees=[0, 1],
            sub_note=None,
        ),
        dict(
            title='إطلاق حملة توعوية رقمية حول خدمات المركز',
            description='تنظيم وإطلاق حملة توعوية رقمية عبر منصات التواصل الاجتماعي (فيسبوك، إنستغرام، يوتيوب) للتعريف بخدمات المركز الوطني للوثائق التربوية للعام الدراسي 2025-2026، مع رصد وتحليل مؤشرات التفاعل والوصول.',
            priority='critical', status='in_progress', progress=40,
            deadline_days=15,
            assignees=[1, 2],
            sub_note='تم إعداد خطة الحملة وجدول النشر وانطلق النشر على الفيسبوك.',
        ),
    ],
    'mod-3e7e10e1': [
        dict(
            title='توزيع الكتب المدرسية الإلكترونية على المديريات – الطور الابتدائي',
            description='التنسيق مع مديريات التربية في 10 ولايات لتوزيع الكتب المدرسية الرقمية للطور الابتدائي (السنة الأولى والثانية) عبر المنصة الإلكترونية للمركز. يشمل: إنشاء حسابات المديريات، تحميل الموارد، والتحقق من إمكانية الوصول.',
            priority='critical', status='in_progress', progress=70,
            deadline_days=7,
            assignees=[0, 3],
            sub_note='تم إتمام التوزيع في 7 ولايات من أصل 10، جارٍ العمل في الولايات المتبقية.',
        ),
        dict(
            title='إعداد كتالوج الإصدارات الجديدة 2025',
            description='إعداد كتالوج إلكتروني وورقي شامل للإصدارات الجديدة للمركز خلال سنة 2025، يتضمن: الوثائق التربوية، الدلائل المنهجية، المجلات العلمية، والموارد الرقمية. مع تصنيف واضح حسب المراحل الدراسية والمجالات.',
            priority='medium', status='submitted', progress=100,
            deadline_days=3,
            assignees=[2],
            sub_note='اكتمل الكتالوج وتم رفع النسخة الإلكترونية PDF للمراجعة النهائية.',
        ),
        dict(
            title='تحليل إحصاءات توزيع الوثائق الفصل الثالث 2025',
            description='استخلاص وتحليل إحصاءات توزيع الوثائق والمطبوعات التربوية خلال الفصل الثالث من سنة 2025، وإعداد تقرير مفصل يتضمن: حجم التوزيع حسب الولايات، أنواع الوثائق الأكثر طلباً، ومقارنة بالفصل المماثل من السنة الماضية.',
            priority='high', status='approved', progress=100,
            deadline_days=-5,
            assignees=[1],
            sub_note='تقرير الإحصاءات مكتمل ومعتمد. نسبة التوزيع ارتفعت بـ 18% عن الفصل الماضي.',
        ),
        dict(
            title='معالجة طلبات الحصول على الوثائق الواردة إلكترونياً',
            description='معالجة مجموعة طلبات الحصول على الوثائق التربوية الواردة عبر البريد الإلكتروني والمنصة الرقمية خلال الفترة من 1 إلى 15 أكتوبر 2025، والتأكد من الرد على كل طلب خلال 48 ساعة من وروده.',
            priority='high', status='in_progress', progress=55,
            deadline_days=4,
            assignees=[0, 2],
            sub_note='تم معالجة 23 طلباً من أصل 41 طلباً وارداً.',
        ),
        dict(
            title='تجديد اتفاقيات التوزيع مع المكتبات الجامعية',
            description='مراجعة وتجديد اتفاقيات توزيع الوثائق التربوية مع 15 مكتبة جامعية في مختلف أنحاء الوطن، وتحديث شروط التعاون بما يتوافق مع السياسة الجديدة للمركز للعام 2025-2026.',
            priority='medium', status='pending', progress=10,
            deadline_days=30,
            assignees=[3],
            sub_note=None,
        ),
    ],
    'mod-a6d2055c': [
        dict(
            title='تنظيم الاستقبال الرسمي لوفد منظمة اليونسكو',
            description='التحضير الكامل لاستقبال وفد منظمة اليونسكو الزائر للمركز الوطني للوثائق التربوية في إطار برنامج التعاون التربوي الدولي، يشمل: إعداد برنامج الزيارة، الحزم التعريفية، العروض التقديمية، والترتيبات اللوجستية.',
            priority='critical', status='submitted', progress=100,
            deadline_days=2,
            assignees=[0, 1],
            sub_note='تم إعداد جميع المستلزمات والبرنامج الكامل للزيارة وإرساله للمراجعة.',
        ),
        dict(
            title='إعداد التقرير السنوي للعلاقات العامة 2024-2025',
            description='إعداد التقرير السنوي الشامل لأنشطة مصلحة العلاقات العامة للسنة الدراسية 2024-2025، يتضمن: ملخص الفعاليات، الشراكات المبرمة، الزيارات الرسمية، والمبادرات الإعلامية والتوثيقية.',
            priority='high', status='in_progress', progress=75,
            deadline_days=12,
            assignees=[2, 3],
            sub_note='تم إنجاز الفصلين الأول والثاني من التقرير وإرساله للمراجعة الأولية.',
        ),
        dict(
            title='تحديث بروتوكول الشراكات المؤسسية',
            description='مراجعة وتحديث وثيقة بروتوكول الشراكات المؤسسية للمركز بما يتوافق مع المستجدات والتوجيهات الوزارية لسنة 2025، مع توثيق الشراكات القائمة وتحديد آفاق الشراكات الجديدة المرتقبة.',
            priority='medium', status='approved', progress=100,
            deadline_days=-3,
            assignees=[1],
            sub_note='تم اعتماد البروتوكول المحدث ورفعه للأمانة العامة.',
        ),
        dict(
            title='إطار اتفاقية تعاون مع وزارة التعليم العالي',
            description='إعداد الإطار القانوني والتقني لاتفاقية تعاون بين المركز الوطني للوثائق التربوية ووزارة التعليم العالي والبحث العلمي في مجال توثيق ونشر الأبحاث التربوية الجامعية على المستوى الوطني.',
            priority='high', status='in_progress', progress=35,
            deadline_days=25,
            assignees=[0, 2],
            sub_note='تم إعداد الفصل الأول من الإطار القانوني وإرساله للمراجعة.',
        ),
        dict(
            title='تنظيم اليوم المفتوح للمركز – نوفمبر 2025',
            description='التخطيط والتنظيم الكامل لليوم المفتوح السنوي للمركز الوطني للوثائق التربوية المقرر في نوفمبر 2025، يشمل: برمجة ورشات العمل، معارض الوثائق، الندوات التعريفية بخدمات المركز، ودعوة ممثلي مديريات التربية الوطنية.',
            priority='high', status='pending', progress=20,
            deadline_days=35,
            assignees=[1, 3],
            sub_note=None,
        ),
    ],
}

# ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
# 4.  INSERT TASKS + SUBMISSIONS
# ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
now = timezone.now()
today = date.today()

total_tasks = 0
total_subs  = 0

for mod in modules:
    scenarios = TASK_SCENARIOS.get(mod.slug)
    if not scenarios:
        print(f"No scenario for module: {mod.name} ({mod.slug})")
        continue

    print(f"\nModule: {mod.name}")
    for sc in scenarios:
        deadline = now + timedelta(days=sc['deadline_days'])
        task = Task.objects.create(
            work_module     = mod,
            title           = sc['title'],
            description     = sc['description'],
            priority        = sc['priority'],
            status          = sc['status'],
            progress        = sc['progress'],
            task_type       = 'standard',
            created_by      = manager_user,
            start_date      = today,
            deadline        = deadline,
            estimated_hours = random.choice([4, 8, 12, 16, 24]),
            kpi_weight      = random.choice([1.0, 2.0, 3.0]),
        )
        for idx in sc['assignees']:
            task.assigned_to.add(workers[idx])
        task.save()
        total_tasks += 1
        print(f"  Task created: {task.title[:60]}")

        if sc.get('sub_note'):
            worker = workers[sc['assignees'][0]]
            sub_status = {
                'submitted':   'submitted',
                'approved':    'approved',
                'in_progress': 'submitted',
                'completed':   'approved',
            }.get(sc['status'], 'submitted')

            sub = Submission.objects.create(
                task         = task,
                worker       = worker,
                notes        = sc['sub_note'],
                status       = sub_status,
                progress     = sc['progress'],
                submitted_at = now - timedelta(hours=random.randint(1, 72)),
            )
            if sub_status == 'approved':
                sub.reviewed_by      = manager_user
                sub.reviewed_at      = now - timedelta(hours=random.randint(1, 24))
                sub.manager_feedback = 'تمت المراجعة والموافقة على العمل المقدم. شكراً على الإنجاز في الوقت المحدد.'
                sub.score            = random.choice([85.0, 90.0, 95.0, 100.0])
                sub.save()

            SubmissionComment.objects.create(
                submission = sub,
                author     = worker,
                comment    = sc['sub_note'],
            )
            total_subs += 1
            print(f"    Submission ({sub.status}) by {worker.first_name} {worker.last_name}")

print(f"\n{'='*60}")
print(f"Seed complete:")
print(f"  Users   : {len(created_users)}")
print(f"  Tasks   : {total_tasks}")
print(f"  Submissions: {total_subs}")
print(f"{'='*60}")
