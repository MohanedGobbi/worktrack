"""Remove duplicate sidebar rules (older installs have several rows per feature key)."""
from django.db import migrations


def dedupe(apps, schema_editor):
    Rule = apps.get_model('users', 'SidebarVisibilityRule')
    seen = set()
    for rule in Rule.objects.order_by('id'):
        if rule.feature_key in seen:
            rule.delete()
        else:
            seen.add(rule.feature_key)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_v1_hidden_features'),
    ]

    operations = [
        migrations.RunPython(dedupe, migrations.RunPython.noop),
    ]
