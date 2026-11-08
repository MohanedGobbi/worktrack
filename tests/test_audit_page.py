from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from audit.models import ActivityLog

User = get_user_model()


class AuditLogPageTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='a@t.local', password='x', username='a', role='super_admin', first_name='Ada')
        self.mgr = User.objects.create_user(email='m@t.local', password='x', username='m', role='manager')
        ActivityLog.objects.create(user=self.admin, action='create', object_type='Task', object_id=1, object_str='Report', description='Created task Report', ip_address='10.0.0.5')
        ActivityLog.objects.create(user=self.admin, action='delete', object_type='User', object_id=2, object_str='bob', description='Deleted bob')

    def test_administrators_only(self):
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(reverse('audit-logs')).status_code, 302)
        self.client.force_login(self.admin)
        r = self.client.get(reverse('audit-logs'))
        self.assertContains(r, 'Created task Report')
        self.assertContains(r, '10.0.0.5')

    def test_filters(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('audit-logs'), {'action': 'delete'})
        self.assertContains(r, 'Deleted bob')
        self.assertNotContains(r, 'Created task Report')
        r = self.client.get(reverse('audit-logs'), {'search': 'Report', 'user': self.admin.id})
        self.assertContains(r, 'Created task Report')
        self.assertNotContains(r, 'Deleted bob')

    def test_description_is_escaped(self):
        ActivityLog.objects.create(user=self.admin, action='update', object_type='Task', object_id=3, description='<img src=x onerror=alert(1)>')
        self.client.force_login(self.admin)
        r = self.client.get(reverse('audit-logs'))
        self.assertNotContains(r, '<img src=x onerror')
