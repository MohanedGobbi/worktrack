import os
import re
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase

User = get_user_model()


def run(*args, env=None):
    out = StringIO()
    with mock.patch.dict(os.environ, env or {}, clear=False):
        if not env:
            os.environ.pop('WT_SUPPORT_PASSWORD', None)
        call_command('support_admin', *args, stdout=out)
    return out.getvalue()


class SupportAdminTests(TestCase):
    def test_creates_super_admin_and_prints_password_once(self):
        out = run('--email', 'support@rowd.test')
        user = User.objects.get(email='support@rowd.test')
        password = re.search(r'Password for support@rowd.test: (\S+)', out).group(1)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_superuser and user.is_staff and user.is_active)
        self.assertEqual(user.role, 'super_admin')
        self.assertEqual(user.first_name, 'ROWD')

    def test_restores_a_disabled_or_demoted_account_and_keeps_password(self):
        run('--email', 'support@rowd.test', env={'WT_SUPPORT_PASSWORD': 'Long-Support-Pass-1'})
        User.objects.filter(email='support@rowd.test').update(is_active=False, is_superuser=False, is_staff=False, role='worker')
        out = run('--email', 'support@rowd.test')
        user = User.objects.get(email='support@rowd.test')
        self.assertIn('restored', out)
        self.assertNotIn('Password for', out)
        self.assertTrue(user.is_active and user.is_superuser and user.is_staff)
        self.assertEqual(user.role, 'super_admin')
        self.assertTrue(user.check_password('Long-Support-Pass-1'))

    def test_reset_password(self):
        run('--email', 'support@rowd.test', env={'WT_SUPPORT_PASSWORD': 'Long-Support-Pass-1'})
        out = run('--email', 'support@rowd.test', '--reset-password')
        password = re.search(r'Password for support@rowd.test: (\S+)', out).group(1)
        self.assertTrue(User.objects.get(email='support@rowd.test').check_password(password))

    def test_short_env_password_refused(self):
        with self.assertRaises(CommandError):
            run('--email', 'support@rowd.test', env={'WT_SUPPORT_PASSWORD': 'short'})
        self.assertFalse(User.objects.filter(email='support@rowd.test').exists())
