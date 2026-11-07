from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import SiteConfiguration
from users.models import SiteSettings

User = get_user_model()


def _post(**over):
    data = {
        'app_name': 'Test University', 'app_name_ar': 'جامعة الاختبار',
        'theme_preset': 'custom', 'primary_color': '#047857', 'accent_color': '#34D399', 'on_brand_color': '#fff',
        'contact_email': 'info@uni.test', 'contact_phone': '+213 555', 'website_url': 'https://uni.test',
        'address': '', 'address_ar': '', 'footer_text': '', 'footer_text_ar': 'جامعة الاختبار · الإدارة',
        'default_language': 'en', 'allow_registration': '',
    }
    data.update(over)
    return data


class SiteSettingsViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='sa@t.local', password='x', username='sa', role='super_admin')
        self.url = reverse('site-settings')

    def test_requires_super_admin(self):
        mgr = User.objects.create_user(email='m@t.local', password='x', username='m', role='manager')
        self.client.force_login(mgr)
        self.assertNotEqual(self.client.get(self.url).status_code, 200)

    def test_save_applies_theme_everywhere(self):
        self.client.force_login(self.admin)
        r = self.client.post(self.url, _post())
        self.assertEqual(r.status_code, 302)
        c = SiteConfiguration.objects.get()
        self.assertEqual((c.theme_preset, c.primary_color, c.accent_color, c.on_brand_color), ('custom', '#047857', '#34d399', '#ffffff'))
        s = SiteSettings.get_settings()
        self.assertEqual(s.default_language, 'en')
        self.assertFalse(s.allow_registration)
        page = self.client.get(reverse('dashboard'))
        self.assertContains(page, '--wt-brand: #047857')
        self.assertContains(page, 'info@uni.test')
        self.assertContains(page, 'Built by')  # the ROWD credit never goes away

    def test_rowd_preset_ignores_custom_colours(self):
        self.client.force_login(self.admin)
        self.client.post(self.url, _post(theme_preset='rowd'))
        self.assertContains(self.client.get(reverse('dashboard')), '--wt-brand: #0033a0')

    def test_bad_colour_rejected(self):
        self.client.force_login(self.admin)
        r = self.client.post(self.url, _post(primary_color='red;}body{x'))
        self.assertEqual(r.status_code, 200)
        self.assertNotEqual(SiteConfiguration.objects.get().primary_color, 'red;}body{x')

    def test_page_renders(self):
        self.client.force_login(self.admin)
        r = self.client.get(self.url)
        self.assertContains(r, 'id="ss-preview"')
        self.assertContains(r, 'name="on_brand_color"')
