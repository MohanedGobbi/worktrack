from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_translationitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemLimits',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                # ── User counts ───────────────────────────────────────────────────
                ('max_users',         models.PositiveIntegerField(default=10,    help_text='Maximum total active users in the system')),
                ('max_admins',        models.PositiveIntegerField(default=2,     help_text='Maximum users with admin or super_admin role')),
                ('max_managers',      models.PositiveIntegerField(default=5,     help_text='Maximum users with manager role')),
                ('max_workers',       models.PositiveIntegerField(default=20,    help_text='Maximum users with worker role')),
                # ── Task & work ───────────────────────────────────────────────────
                ('max_tasks',         models.PositiveIntegerField(default=100,   help_text='Maximum total tasks in the system')),
                ('max_submissions',   models.PositiveIntegerField(default=500,   help_text='Maximum task submissions / reports')),
                ('max_work_modules',  models.PositiveIntegerField(default=5,     help_text='Maximum work modules / projects')),
                # ── Messaging & notifications ─────────────────────────────────────
                ('max_messages',      models.PositiveIntegerField(default=1000,  help_text='Maximum chat / direct messages')),
                ('max_notifications', models.PositiveIntegerField(default=5000,  help_text='Maximum notification records')),
                # ── Storage ───────────────────────────────────────────────────────
                ('max_storage_mb',    models.PositiveIntegerField(default=500,   help_text='Maximum total media storage (MB)')),
                ('max_file_size_mb',  models.PositiveIntegerField(default=10,    help_text='Maximum single file upload size (MB)')),
                # ── Audit ─────────────────────────────────────────────────────────
                ('max_audit_logs',    models.PositiveIntegerField(default=10000, help_text='Maximum audit log entries kept')),
                # ── Meta ─────────────────────────────────────────────────────────
                ('is_active',         models.BooleanField(default=True,          help_text='Enable / disable limit enforcement globally')),
                ('created_at',        models.DateTimeField(auto_now_add=True)),
                ('updated_at',        models.DateTimeField(auto_now=True)),
                ('notes',             models.TextField(blank=True, default='',   help_text='Optional notes about this configuration')),
            ],
            options={
                'verbose_name': 'System Limits',
                'verbose_name_plural': 'System Limits',
            },
        ),
    ]
