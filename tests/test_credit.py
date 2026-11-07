"""The ROWD Tech credit must appear on every public page and in the app shell, for every install and theme."""
from django.test import TestCase, Client, override_settings
from django.conf import settings
from users.models import CustomUser


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class RowdCreditTests(TestCase):
    PUBLIC = ['/', '/login/', '/register/', '/password_reset/']

    def setUp(self):
        settings.ALLOWED_HOSTS = ['*']

    def test_public_pages_carry_credit(self):
        c = Client(HTTP_HOST='127.0.0.1')
        for path in self.PUBLIC:
            html = c.get(path).content.decode('utf-8', 'ignore')
            self.assertIn('rowd_logo', html, f'ROWD credit missing on {path}')
            self.assertIn('ROWD Tech', html, f'ROWD credit missing on {path}')

    def test_app_shell_carries_credit(self):
        user = CustomUser.objects.create_user(email='credit@test.com', password='TestPass123!', role='manager')
        c = Client(HTTP_HOST='127.0.0.1')
        c.force_login(user)
        html = c.get('/tasks/').content.decode('utf-8', 'ignore')
        self.assertGreaterEqual(html.count('wt-credit'), 2, 'ROWD credit must appear in sidebar and footer')
