import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import Department

User = get_user_model()


def _u(email, role='worker', **kw):
    return User.objects.create_user(email=email, password='Old-pass-123!', username=email, role=role, first_name='A', **kw)


def _form(**over):
    d = {'email': 'new@t.local', 'first_name': 'Sara', 'last_name': 'B', 'role': 'worker', 'password': 'Brand-new-pass-9',
         'department': '', 'new_department': '', 'manager': '', 'position': '', 'phone': '', 'bio': '',
         'email_notifications': 'on'}
    d.update(over)
    return d


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='wt-users-media-'))
class UserAdminTests(TestCase):
    def setUp(self):
        self.admin = _u('admin@t.local', 'super_admin')
        self.client.force_login(self.admin)

    def tearDown(self):
        from django.conf import settings
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_only_super_admin(self):
        mgr = _u('m@t.local', 'manager')
        self.client.force_login(mgr)
        self.assertEqual(self.client.get(reverse('user-management')).status_code, 302)
        self.assertEqual(self.client.post(reverse('user-create'), _form()).status_code, 302)
        self.assertFalse(User.objects.filter(email='new@t.local').exists())

    def test_create_with_department_and_flags(self):
        r = self.client.post(reverse('user-create'), _form(role='super_admin', new_department='Rectorate'))
        self.assertEqual(r.status_code, 302)
        u = User.objects.get(email='new@t.local')
        self.assertEqual((u.role, u.is_superuser, u.is_staff, u.department.name), ('super_admin', True, True, 'Rectorate'))
        self.assertTrue(u.check_password('Brand-new-pass-9'))

    def test_weak_password_and_duplicate_email_rejected(self):
        r = self.client.post(reverse('user-create'), _form(password='12345678'))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(email='new@t.local').exists())
        _u('taken@t.local')
        r = self.client.post(reverse('user-create'), _form(email='TAKEN@t.local'))
        self.assertContains(r, 'already uses this email')

    def test_edit_keeps_password_when_empty_and_syncs_flags(self):
        w = _u('w@t.local')
        self.client.post(reverse('user-edit', args=[w.id]), _form(email='w@t.local', password='', role='manager'))
        w.refresh_from_db()
        self.assertEqual(w.role, 'manager')
        self.assertTrue(w.check_password('Old-pass-123!'))
        self.assertFalse(w.is_superuser)

    def test_cannot_demote_only_admin(self):
        r = self.client.post(reverse('user-edit', args=[self.admin.id]), _form(email='admin@t.local', password='', role='worker'))
        self.assertEqual(r.status_code, 200)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, 'super_admin')

    def test_cannot_deactivate_self_or_delete_only_admin(self):
        r = self.client.post(reverse('user-toggle-status', args=[self.admin.id]), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 400)
        other = _u('o@t.local', 'super_admin')
        self.client.force_login(other)
        self.admin.is_active = False
        self.admin.save()
        r = self.client.post(reverse('user-delete', args=[other.id]), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 400)

    def test_list_filters(self):
        _u('findme@t.local')
        r = self.client.get(reverse('user-management'), {'search': 'findme'})
        self.assertContains(r, 'findme@t.local')
        self.assertNotContains(r, 'admin@t.local</small>')

    def test_photo_is_reencoded_and_html_rejected(self):
        from PIL import Image
        buf = BytesIO()
        Image.new('RGB', (20, 20), 'red').save(buf, 'GIF')
        evil = SimpleUploadedFile('x.html', buf.getvalue() + b'<script>alert(1)</script>', content_type='text/html')
        self.client.post(reverse('user-create'), {**_form(), 'avatar': evil})
        u = User.objects.get(email='new@t.local')
        name = u.profile.avatar.name
        self.assertRegex(name, r'^avatars/[0-9a-f]{32}\.(jpg|png)$')
        self.assertNotIn(b'<script>', u.profile.avatar.read())
        junk = SimpleUploadedFile('y.png', b'<html>not an image</html>', content_type='image/png')
        r = self.client.post(reverse('user-create'), {**_form(email='two@t.local'), 'avatar': junk})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(email='two@t.local').exists())

    def test_impersonation_needs_post(self):
        w = _u('imp@t.local')
        self.assertEqual(self.client.get(reverse('impersonate-user', args=[w.id])).status_code, 405)
        self.client.post(reverse('impersonate-user', args=[w.id]))
        self.assertEqual(self.client.get(reverse('dashboard'), follow=True).context['user'].id, w.id)
