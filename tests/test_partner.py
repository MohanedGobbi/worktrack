import json
import shutil
import tempfile
from io import BytesIO, StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import SiteConfiguration

User = get_user_model()


def _png():
    from PIL import Image
    buf = BytesIO()
    Image.new('RGBA', (60, 30), (17, 99, 51, 255)).save(buf, 'PNG')
    return buf.getvalue()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='wt-partner-'))
class PartnerTests(TestCase):
    def tearDown(self):
        from django.conf import settings
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_partner_shows_beside_the_rowd_credit(self):
        admin = User.objects.create_user(email='a@t.local', password='x', username='a', role='super_admin')
        self.client.force_login(admin)
        data = {'app_name': 'Uni', 'app_name_ar': 'جامعة', 'theme_preset': 'rowd', 'primary_color': '#116333',
                'accent_color': '#7dc35b', 'on_brand_color': '#ffffff', 'default_language': 'ar',
                'partner_name': 'AFAK', 'partner_name_ar': 'مؤسسة آفاق', 'partner_url': 'https://afak.example',
                'partner_logo': SimpleUploadedFile('afak.png', _png(), content_type='image/png')}
        self.assertEqual(self.client.post(reverse('site-settings'), data).status_code, 302)
        c = SiteConfiguration.objects.get()
        self.assertRegex(c.partner_logo.name, r'^site/partners/[0-9a-f]{32}\.png$')
        for page in (reverse('dashboard'), '/', reverse('login')):
            self.client.logout() if page != reverse('dashboard') else None
            html = self.client.get(page).content.decode()
            self.assertIn('In partnership with', html, page)
            self.assertIn('href="https://afak.example"', html, page)
            self.assertIn('wt-credit', html, page)  # the ROWD credit is still there
            self.assertIn('ROWD Tech', html, page)

    def test_new_institution_sets_banner_and_partner(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ('logo.png', 'banner.png', 'partner.png'):
                (Path(d) / name).write_bytes(_png())
            cfg = {'name': 'Uni', 'name_ar': 'جامعة', 'logo': 'logo.png', 'banner': 'banner.png',
                   'partner': {'name': 'AFAK', 'name_ar': 'آفاق', 'url': 'https://afak.example', 'logo': 'partner.png'}}
            (Path(d) / 'c.json').write_text(json.dumps(cfg), encoding='utf-8')
            call_command('new_institution', '--config', str(Path(d) / 'c.json'), stdout=StringIO())
        c = SiteConfiguration.objects.get()
        self.assertTrue(c.banner_image and c.partner_logo and c.logo)
        self.assertEqual((c.partner_name, c.partner_url), ('AFAK', 'https://afak.example'))
