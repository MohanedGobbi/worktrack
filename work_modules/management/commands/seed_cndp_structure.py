import os
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from work_modules.models import WorkGroup, WorkModule
from core.models import SiteConfiguration

class Command(BaseCommand):
    help = 'Seeds the official CNDP organizational structure (Groups and Modules)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Initializing CNDP Organizational Structure..."))

        # Update SiteConfiguration app name if default
        config, _ = SiteConfiguration.objects.get_or_create()
        config.app_name = "المركز الوطني للوثائق التربوية CNDP"
        if not config.theme_preset or config.theme_preset == 'custom':
            config.theme_preset = 'crimson'
            config.primary_color = '#dc2626'
            config.secondary_color = '#1e1e1e'
            config.portal_bg_color = '#0b0f19'
        config.save()

        # CNDP Groups & Modules Definition
        cndp_groups = [
            {
                'name': 'القيادة والتوجيه',
                'name_en': 'Leadership & Direction',
                'slug': 'leadership-direction',
                'description': 'المجلس التوجيهي، إدارة المركز، اللجنة التقنية، العون المحاسب',
                'icon_class': 'fa-compass',
                'color': '#dc2626',
                'bg_color': '#1f191d',
                'order': 1,
                'modules': [
                    {'name': 'مجلس التوجيه', 'icon': 'fa-users-cog', 'desc': 'توجيه واستراتيجية المركز الوطني للوثائق التربوية'},
                    {'name': 'مدير المركز', 'icon': 'fa-user-tier', 'desc': 'الإدارة العامة والقرارات التنفيذية'},
                    {'name': 'العون المحاسب', 'icon': 'fa-calculator', 'desc': 'المحاسبة المالية والرقابة المالية'},
                    {'name': 'اللجنة التقنية', 'icon': 'fa-cogs', 'desc': 'الدراسات والتقييم التقني للوثائق والوسائط'},
                ]
            },
            {
                'name': 'الإدارة والوسائل',
                'name_en': 'Administration & Resources',
                'slug': 'administration-resources',
                'description': 'الأمانة العامة، الموارد البشرية، المحاسبة والمالية',
                'icon_class': 'fa-sitemap',
                'color': '#e11d48',
                'bg_color': '#1f191d',
                'order': 2,
                'modules': [
                    {'name': 'الأمانة العامة', 'icon': 'fa-file-signature', 'desc': 'إدارة التنسيق والبريد الإداري العام'},
                    {'name': 'قسم الموارد البشرية والوسائل العامة', 'icon': 'fa-user-check', 'desc': 'تسيير الموظفين والوسائل اللوجستية'},
                    {'name': 'قسم المحاسبة والمالية', 'icon': 'fa-file-invoice-dollar', 'desc': 'الميزانية والميزانيات التشغيلية'},
                ]
            },
            {
                'name': 'الإعلام التربوي والاتصال',
                'name_en': 'Educational Media & Communication',
                'slug': 'educational-media-communication',
                'description': 'الإعلام والاتصال، النشر والتوزيع، العلاقات العامة والتوثيق',
                'icon_class': 'fa-bullhorn',
                'color': '#b91c1c',
                'bg_color': '#1f191d',
                'order': 3,
                'modules': [
                    {'name': 'قسم الإعلام والاتصال التربوي', 'icon': 'fa-broadcast-tower', 'desc': 'الإعلام التربوي والاتصال المؤسساتي'},
                    {'name': 'مصلحة النشر والتوزيع', 'icon': 'fa-print', 'desc': 'نشر وتوزيع الوثائق والمنشورات التربوية'},
                    {'name': 'مصلحة العلاقات العامة والتوثيق', 'icon': 'fa-handshake', 'desc': 'العلاقات العامة والشراكات والتوثيق'},
                ]
            },
            {
                'name': 'إنتاج وتطوير الوسائط التربوية',
                'name_en': 'Production & Development of Educational Media',
                'slug': 'media-production-development',
                'description': 'الوسائط التعليمية، الموارد الرقمية، الوسائل الديداكتيكية',
                'icon_class': 'fa-photo-video',
                'color': '#991b1b',
                'bg_color': '#1f191d',
                'order': 4,
                'modules': [
                    {'name': 'قسم الوسائط التعليمية والمطبوعات', 'icon': 'fa-photo-video', 'desc': 'تصميم وإعداد المطبوعات والوسائط التعليمية'},
                    {'name': 'مصلحة إنتاج الموارد الرقمية', 'icon': 'fa-laptop-code', 'desc': 'إنتاج المحتوى الرقمي والبرمجيات التفاعلية'},
                    {'name': 'مصلحة الوسائل الديداكتيكية', 'icon': 'fa-tools', 'desc': 'تطوير وتوفير الوسائل التوضيحية والديداكتيكية'},
                ]
            },
            {
                'name': 'التوثيق والأرشيف',
                'name_en': 'Documentation & Archives',
                'slug': 'documentation-archives',
                'description': 'التوثيق والأرشيف التربوي، الأرشيف الوطني، المكتبات',
                'icon_class': 'fa-archive',
                'color': '#7f1d1d',
                'bg_color': '#1f191d',
                'order': 5,
                'modules': [
                    {'name': 'قسم التوثيق والأرشيف التربوي', 'icon': 'fa-archive', 'desc': 'حفظ ومعالجة الرصيد التوثيقي التربوي'},
                    {'name': 'مصلحة الأرشيف الوطني التربوي', 'icon': 'fa-vault', 'desc': 'فهرسة وتخزين الأرشيف التاريخي التربوي'},
                    {'name': 'مصلحة التوثيق والمكتبات', 'icon': 'fa-book-reader', 'desc': 'إدارة المكتبة الوطنية التربوية والمراجع'},
                ]
            },
            {
                'name': 'الفروع الجهوية',
                'name_en': 'Regional Branches',
                'slug': 'regional-branches',
                'description': 'ملحقات ومراكز التوثيق التربوي عبر الولايات',
                'icon_class': 'fa-map-marked-alt',
                'color': '#450a0a',
                'bg_color': '#1f191d',
                'order': 6,
                'modules': [
                    {'name': 'ملحقات ومراكز التوثيق عبر الولايات', 'icon': 'fa-building-flag', 'desc': 'شبكة المراكز والملحقات الجهوية للتوثيق التربوي'},
                ]
            }
        ]

        for g_data in cndp_groups:
            group, created = WorkGroup.objects.update_or_create(
                slug=g_data['slug'],
                defaults={
                    'name': g_data['name'],
                    'description': g_data['description'],
                    'icon_class': g_data['icon_class'],
                    'color': g_data['color'],
                    'bg_color': g_data['bg_color'],
                    'order': g_data['order'],
                }
            )
            action_str = "Created" if created else "Updated"
            self.stdout.write(f"  [{action_str} Group] {group.name}")

            for idx, m_data in enumerate(g_data['modules'], start=1):
                mod_slug = slugify(m_data['name'])
                if not mod_slug:
                    import uuid
                    mod_slug = f"mod-{uuid.uuid4().hex[:8]}"

                module, mod_created = WorkModule.objects.update_or_create(
                    name=m_data['name'],
                    defaults={
                        'slug': mod_slug,
                        'icon_class': m_data['icon'],
                        'color': g_data['color'],
                        'description': m_data['desc'],
                        'group_link': group,
                        'group': group.name,
                        'order': idx,
                    }
                )
                mod_action = "Created" if mod_created else "Updated"
                self.stdout.write(f"    - [{mod_action} Module] {module.name}")

        self.stdout.write(self.style.SUCCESS("CNDP Structure Seeded Successfully!"))
