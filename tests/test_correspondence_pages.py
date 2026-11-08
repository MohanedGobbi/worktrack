import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from tasks.models import Correspondence, CorrespondenceAcknowledgement
from work_modules.models import WorkGroup

User = get_user_model()


def _u(email, role='worker', **kw):
    return User.objects.create_user(email=email, password='x', username=email, role=role, first_name=email.split('@')[0], **kw)


def _data(**over):
    d = {'title': 'Exam timetable', 'description': 'Please read.', 'correspondence_type': 'circular', 'priority': 'high',
         'reference_number': 'REF/1', 'deadline': '2030-01-31', 'work_module': ''}
    d.update(over)
    return d


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='wt-corr-media-'))
class CorrespondencePagesTests(TestCase):
    def setUp(self):
        self.admin = _u('admin@t.local', 'super_admin')
        self.mgr = _u('mgr@t.local', 'manager')
        self.w1, self.w2 = _u('w1@t.local'), _u('w2@t.local')
        self.outsider = _u('out@t.local')
        g = WorkGroup.objects.create(name='Team', slug='team')
        for u in (self.mgr, self.w1, self.w2):
            g.members.add(u)

    def tearDown(self):
        from django.conf import settings
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def issue(self, user, **over):
        self.client.force_login(user)
        return self.client.post(reverse('correspondence-create'), _data(**over))

    def test_manager_issues_to_teammates_and_item_without_module_is_listed(self):
        r = self.issue(self.mgr, assigned_to=[self.w1.id, self.w2.id])
        self.assertEqual(r.status_code, 302)
        c = Correspondence.objects.get()
        self.assertEqual((c.created_by, c.assigned_to.count(), c.work_module), (self.mgr, 2, None))
        self.assertContains(self.client.get(reverse('admin-correspondence')), 'Exam timetable')

    def test_recipients_outside_the_team_are_rejected(self):
        r = self.issue(self.mgr, assigned_to=[self.outsider.id])
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Correspondence.objects.exists())

    def test_worker_sees_only_own_and_can_acknowledge_once(self):
        self.issue(self.mgr, assigned_to=[self.w1.id])
        c = Correspondence.objects.get()
        self.client.force_login(self.w2)
        self.assertEqual(self.client.get(reverse('correspondence-detail', args=[c.pk])).status_code, 302)
        self.assertNotContains(self.client.get(reverse('admin-correspondence')), 'Exam timetable')
        self.client.force_login(self.w1)
        self.assertContains(self.client.get(reverse('admin-correspondence')), 'Waiting for you')
        self.client.post(reverse('correspondence-acknowledge', args=[c.pk]), {'note': 'ok'})
        self.client.post(reverse('correspondence-acknowledge', args=[c.pk]))
        self.assertEqual(CorrespondenceAcknowledgement.objects.filter(correspondence=c).count(), 1)
        self.assertContains(self.client.get(reverse('correspondence-detail', args=[c.pk])), 'You acknowledged this')

    def test_workers_cannot_create_edit_or_delete(self):
        self.issue(self.mgr, assigned_to=[self.w1.id])
        c = Correspondence.objects.get()
        self.client.force_login(self.w1)
        self.client.post(reverse('correspondence-create'), _data(title='Nope'))
        self.client.post(reverse('correspondence-edit', args=[c.pk]), _data(title='Changed'))
        self.client.post(reverse('correspondence-delete', args=[c.pk]))
        c.refresh_from_db()
        self.assertEqual(c.title, 'Exam timetable')
        self.assertEqual(Correspondence.objects.count(), 1)

    def test_another_manager_cannot_edit_someone_elses_item(self):
        self.issue(self.mgr, assigned_to=[self.w1.id])
        c = Correspondence.objects.get()
        other = _u('mgr2@t.local', 'manager')
        self.client.force_login(other)
        self.client.post(reverse('correspondence-edit', args=[c.pk]), _data(title='Hijacked'))
        self.client.post(reverse('correspondence-delete', args=[c.pk]))
        self.assertEqual(Correspondence.objects.get().title, 'Exam timetable')

    def test_edit_can_remove_every_recipient(self):
        self.issue(self.mgr, assigned_to=[self.w1.id, self.w2.id])
        c = Correspondence.objects.get()
        self.client.post(reverse('correspondence-edit', args=[c.pk]), _data(status='active'))
        self.assertEqual(c.assigned_to.count(), 0)

    def test_file_types_are_checked(self):
        self.client.force_login(self.mgr)
        bad = SimpleUploadedFile('page.html', b'<script>alert(1)</script>', content_type='text/html')
        r = self.client.post(reverse('correspondence-create'), {**_data(), 'attachment': bad})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Correspondence.objects.exists())
        ok = SimpleUploadedFile('note.txt', b'hello', content_type='text/plain')
        r = self.client.post(reverse('correspondence-create'), {**_data(), 'attachment': ok})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Correspondence.objects.get().attachment.name.endswith('.txt'))
