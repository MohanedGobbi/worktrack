"""Make every email template include the notification text.

Templates used to be created with the first notification's text as their body,
which froze that text into every later email (for example "assigned a new
task: <first task>"). A body with no placeholders at all is such a frozen copy
and is reset; any other body gets {message} appended if it lacks it.
"""
from django.db import migrations

DEFAULT_BODY = 'Hello {recipient_name},\n\n{message}'


def forwards(apps, schema_editor):
    EmailTemplate = apps.get_model('notifications', 'EmailTemplate')
    for t in EmailTemplate.objects.all():
        body = t.body or ''
        if '{message}' in body:
            continue
        if '{' not in body:
            t.body = DEFAULT_BODY
        else:
            t.body = body.rstrip() + '\n\n{message}'
        t.save(update_fields=['body'])


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_emailstyle_emailtemplate'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
