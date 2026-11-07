import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from core.models import SiteConfiguration
from users.models import CustomUser, Department, SidebarVisibilityRule, SiteSettings, SystemProfile


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='wt-test-media-'))
class NewInstitutionTests(TestCase):
    def run_cmd(self, *args):
        out = StringIO()
        call_command('new_institution', *args, stdout=out)
        return out.getvalue()

    def test_full_config(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            Image.new('RGBA', (40, 20), (255, 255, 255, 255)).save(Path(d) / 'logo.png')
            cfg = json.loads((Path(__file__).resolve().parent.parent / 'docs' / 'institution.example.json').read_text(encoding='utf-8'))
            (Path(d) / 'i.json').write_text(json.dumps(cfg), encoding='utf-8')
            out = self.run_cmd('--config', str(Path(d) / 'i.json'))
        c = SiteConfiguration.objects.get()
        self.assertEqual((c.app_name, c.app_name_ar, c.theme_preset, c.primary_color), ('University of Example', 'جامعة المثال', 'custom', '#7a1f2b'))
        self.assertEqual(c.footer_text_ar, 'جامعة المثال · مديرية الإعلام الآلي')
        self.assertTrue(c.logo)
        self.assertEqual(SiteSettings.get_settings().default_language, 'ar')
        self.assertFalse(SiteSettings.get_settings().allow_registration)
        self.assertEqual(Department.objects.count(), 3)
        self.assertEqual(SystemProfile.objects.get(name='Staff').name_ar, 'موظف')
        self.assertFalse(SidebarVisibilityRule.objects.get(feature_key='global_map').is_allowed)
        admin = CustomUser.objects.get(email='admin@example.edu')
        self.assertEqual((admin.role, admin.is_superuser, admin.department.name), ('super_admin', True, 'Rectorate'))
        self.assertIn('Admin password for admin@example.edu', out)
        self.assertTrue(admin.has_usable_password())

    def test_rerun_is_safe_and_keeps_password(self):
        self.run_cmd('--name', 'X', '--departments', 'A,B', '--admin-email', 'a@x.test', '--admin-password', 'S3cret-pass!')
        out = self.run_cmd('--name', 'X2', '--departments', 'A,C', '--admin-email', 'a@x.test')
        self.assertEqual(Department.objects.count(), 3)
        self.assertTrue(CustomUser.objects.get(email='a@x.test').check_password('S3cret-pass!'))
        self.assertEqual(SiteConfiguration.objects.get().app_name, 'X2')
        self.assertNotIn('password for', out)

    def test_rowd_palette_when_no_colours(self):
        self.run_cmd('--name', 'Y')
        self.assertEqual(SiteConfiguration.objects.get().theme_preset, 'rowd')

    def test_light_brand_gets_ink_text(self):
        self.run_cmd('--name', 'Z', '--brand', '#fde68a', '--accent', '#0ea5e9')
        self.assertEqual(SiteConfiguration.objects.get().on_brand_color, '#131925')

    def test_validation_and_dry_run(self):
        with self.assertRaises(CommandError):
            self.run_cmd('--name', 'Bad', '--brand', 'blue', '--accent', '#000')
        with self.assertRaises(CommandError):
            self.run_cmd('--name', 'Half', '--brand', '#000000')
        out = self.run_cmd('--name', 'Dry', '--admin-email', 'd@x.test', '--dry-run')
        self.assertIn('Dry run', out)
        self.assertFalse(CustomUser.objects.filter(email='d@x.test').exists())
        self.assertFalse(SiteConfiguration.objects.filter(app_name='Dry').exists())
