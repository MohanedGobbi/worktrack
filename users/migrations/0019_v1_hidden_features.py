"""Switch off the features the owner left out of v1 (kept in code, switchable in the Admin console)."""
from django.db import migrations

NEW_ROWS = [
    # key, label_en, label_ar, icon, category, admin, manager, worker, order
    ('offline_maps', 'Offline Maps', 'الخرائط دون اتصال', 'fas fa-map', False, True, False, False, 19),
    ('roadmap', 'Roadmap (Gantt)', 'خارطة الطريق', 'fas fa-timeline', False, True, True, False, 20),
    ('templates', 'Module Templates', 'قوالب الوحدات', 'fas fa-clone', False, True, True, False, 21),
    ('todo_management', 'To-do Management', 'إدارة المهام الصغيرة', 'fas fa-list-check', False, True, True, False, 22),
    ('version_archive', 'Version & Data Archive', 'أرشيف النسخ والبيانات', 'fas fa-box-archive', False, True, False, False, 23),
    ('host_management', 'Host Management', 'إدارة المضيفين', 'fas fa-server', False, True, False, False, 24),
    ('messenger_admin', 'Messenger Config and Inspect', 'إعدادات المحادثات والتدقيق', 'fas fa-comments', False, True, False, False, 25),
    ('translations', 'Translation Manager', 'مدير الترجمات', 'fas fa-language', False, True, False, False, 26),
]


def forwards(apps, schema_editor):
    Rule = apps.get_model('users', 'SidebarVisibilityRule')
    if not Rule.objects.exists():
        return  # fresh install: initialize_defaults() creates everything, already switched off
    for key, en, ar, icon, allowed, v_admin, v_mgr, v_wrk, order in NEW_ROWS:
        Rule.objects.update_or_create(
            feature_key=key,
            defaults={'label_en': en, 'label_ar': ar, 'icon': icon, 'category': 'Hidden in v1', 'is_allowed': allowed,
                      'visible_admin': v_admin, 'visible_manager': v_mgr, 'visible_worker': v_wrk, 'order': order})
    Rule.objects.filter(feature_key__in=['global_map', 'org_intelligence']).update(is_allowed=False)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_delete_biogalleryimage_delete_businessmetric_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
