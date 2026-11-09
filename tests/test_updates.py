import json
import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from audit.models import ActivityLog

User = get_user_model()


class UpdateEndpointTests(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='wt-upd-'))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.status_file = self.tmp / 'status' / 'status.json'
        self.status_file.parent.mkdir()
        self.request_dir = self.tmp / 'request'
        self.admin = User.objects.create_user(email='a@t.local', password='Admin-pass-123', username='a', role='super_admin')
        self.manager = User.objects.create_user(email='m@t.local', password='Mgr-pass-123', username='m', role='manager')
        self.settings = override_settings(UPDATE_STATUS_FILE=str(self.status_file), UPDATE_REQUEST_DIR=str(self.request_dir), DEMO_MODE=False)
        self.settings.enable()
        self.addCleanup(self.settings.disable)

    def status(self):
        return self.client.get(reverse('update-status')).json()

    def check(self, password='Admin-pass-123'):
        return self.client.post(reverse('update-check'), {'password': password})

    def test_off_when_not_set_up(self):
        self.client.force_login(self.admin)
        data = self.status()
        self.assertFalse(data['configured'])
        self.assertFalse(data['pending'])
        self.assertEqual(data['status'], {})
        self.assertTrue(data['installed'])
        r = self.check()
        self.assertEqual((r.status_code, r.json()['code']), (409, 'not_configured'))

    def test_reads_the_report(self):
        self.request_dir.mkdir()
        self.status_file.write_text(json.dumps({'state': 'updated', 'installed': '1.0.1', 'latest': '1.0.1',
                                                'message': 'ok', 'timestamp': '2026-11-09T02:14:00Z'}), encoding='utf-8')
        self.client.force_login(self.admin)
        data = self.status()
        self.assertTrue(data['configured'])
        self.assertEqual(data['status']['state'], 'updated')
        self.assertEqual(data['status']['latest'], '1.0.1')

    def test_ignores_garbage(self):
        self.client.force_login(self.admin)
        for junk in ('{not json', json.dumps(['a list']), json.dumps({'state': 'exploded', 'latest': '9'}), ''):
            self.status_file.write_text(junk, encoding='utf-8')
            self.assertEqual(self.status()['status'], {}, junk)
        self.status_file.unlink()
        self.assertEqual(self.status()['status'], {})

    def test_needs_the_password(self):
        self.request_dir.mkdir()
        self.client.force_login(self.admin)
        r = self.check(password='wrong')
        self.assertEqual((r.status_code, r.json()['code']), (403, 'password'))
        self.assertFalse((self.request_dir / 'request').exists())
        r = self.check()
        self.assertEqual(r.status_code, 200)
        self.assertTrue((self.request_dir / 'request').exists())
        self.assertTrue(self.status()['pending'])
        self.assertTrue(ActivityLog.objects.filter(object_type='Software', user=self.admin).exists())

    def test_admin_only(self):
        self.request_dir.mkdir()
        self.assertEqual(self.client.get(reverse('update-status')).status_code, 401)
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse('update-status')).status_code, 403)
        self.assertEqual(self.client.post(reverse('update-check'), {'password': 'Mgr-pass-123'}).status_code, 403)
        self.assertFalse((self.request_dir / 'request').exists())

    def test_refused_in_demo_mode(self):
        self.request_dir.mkdir()
        self.client.force_login(self.admin)
        with override_settings(DEMO_MODE=True):
            r = self.check()
        self.assertEqual((r.status_code, r.json()['code']), (403, 'demo'))
        self.assertFalse((self.request_dir / 'request').exists())

    def test_get_is_not_a_request(self):
        self.request_dir.mkdir()
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('update-check')).status_code, 405)

    def test_health_endpoint(self):
        r = self.client.get(reverse('healthz'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'ok')

    def test_panel_on_site_settings(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('site-settings'))
        self.assertContains(r, 'id="wt-updates"')
        self.assertContains(r, 'id="wt-upd-dialog"')
