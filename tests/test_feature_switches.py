from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from users.models import SidebarVisibilityRule

User = get_user_model()

HIDDEN_V1 = ['global-map', 'offline-map-manager', 'roadmap-gantt', 'template-dashboard', 'version-data-archive',
             'host-management', 'translation-manager', 'organizational-intelligence', 'messaging:config']


class V1HiddenFeatureTests(TestCase):
    def setUp(self):
        SidebarVisibilityRule.initialize_defaults()
        self.admin = User.objects.create_user(email='sa@t.local', password='x', username='sa', role='super_admin')
        self.client.force_login(self.admin)

    def test_defaults_switch_v1_features_off(self):
        off = set(SidebarVisibilityRule.objects.filter(is_allowed=False).values_list('feature_key', flat=True))
        self.assertTrue({'global_map', 'offline_maps', 'roadmap', 'templates', 'todo_management', 'version_archive',
                         'host_management', 'messenger_admin', 'translations', 'org_intelligence'} <= off)

    def test_hidden_pages_redirect_home(self):
        for name in HIDDEN_V1:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302, name)
            self.assertEqual(r['Location'], reverse('dashboard'), name)

    def test_links_are_gone_from_admin_console_and_sidebar(self):
        page = self.client.get(reverse('admin_dashboard')).content.decode()
        for name in ('global-map', 'template-dashboard', 'host-management', 'version-data-archive'):
            self.assertNotIn(f'href="{reverse(name)}"', page, name)
        self.assertNotIn(f'href="{reverse("global-map")}"', self.client.get(reverse('dashboard')).content.decode())

    def test_switching_a_feature_back_on_restores_it(self):
        SidebarVisibilityRule.objects.filter(feature_key='roadmap').update(is_allowed=True)
        self.assertEqual(self.client.get(reverse('roadmap-gantt')).status_code, 200)
