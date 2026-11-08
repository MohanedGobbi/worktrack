from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from tasks.models import Correspondence, Task
from work_modules.models import WorkGroup

User = get_user_model()


def _u(email, role='worker', **kw):
    return User.objects.create_user(email=email, password='Pass-12345-x', username=email, role=role, first_name=email.split('@')[0], **kw)


class UsersApiLockdownTests(TestCase):
    def test_public_registration_cannot_create_an_admin(self):
        r = APIClient().post('/api/users/register/', {'email': 'x@t.local', 'password': 'Pass-12345-x', 'password_confirm': 'Pass-12345-x',
                                                      'first_name': 'X', 'last_name': 'Y', 'role': 'super_admin'}, format='json')
        self.assertIn(r.status_code, (401, 403, 404, 405))
        self.assertFalse(User.objects.filter(email='x@t.local').exists())

    def test_worker_cannot_change_a_role_or_touch_others(self):
        w, other = _u('w@t.local'), _u('o@t.local')
        c = APIClient()
        c.force_authenticate(w)
        c.patch(f'/api/users/{w.id}/', {'role': 'super_admin'}, format='json')
        c.patch(f'/api/users/{other.id}/', {'is_active': False}, format='json')
        self.assertEqual(c.delete(f'/api/users/{other.id}/').status_code, 403)
        w.refresh_from_db(), other.refresh_from_db()
        self.assertEqual(w.role, 'worker')
        self.assertTrue(other.is_active)

    def test_profile_api_cannot_set_manager(self):
        w, boss = _u('w2@t.local'), _u('boss@t.local', 'manager')
        c = APIClient()
        c.force_authenticate(w)
        c.patch('/api/users/profiles/my_profile/', {'manager': boss.id}, format='json')
        from users.models import UserProfile
        p, _ = UserProfile.objects.get_or_create(user=w)
        r = c.patch(f'/api/users/profiles/{p.id}/', {'manager': boss.id, 'position': 'Clerk'}, format='json')
        p.refresh_from_db()
        self.assertIsNone(p.manager_id)


class CorrespondenceReviewTests(TestCase):
    def setUp(self):
        self.mgr = _u('mgr@t.local', 'manager')
        self.ws = [_u(f'w{i}@t.local') for i in range(3)]
        g = WorkGroup.objects.create(name='T', slug='t')
        for u in [self.mgr, *self.ws]:
            g.members.add(u)

    def test_counts_are_the_same_for_workers_and_admins(self):
        c = Correspondence.objects.create(title='Memo', created_by=self.mgr, status='active')
        c.assigned_to.set(self.ws)
        for who in (self.ws[0], self.mgr):
            self.client.force_login(who)
            page = self.client.get(reverse('admin-correspondence')).context['page']
            self.assertEqual(page.object_list[0].wt_total, 3, who.email)

    def test_deleting_a_mirrored_item_sticks(self):
        t = Task.objects.create(title='Legacy circular', description='d', task_type='correspondence', created_by=self.mgr,
                                deadline=timezone.now() + timedelta(days=3))
        t.assigned_to.set(self.ws)
        self.client.force_login(self.mgr)
        self.assertContains(self.client.get(reverse('admin-correspondence')), 'Legacy circular')
        corr = Correspondence.objects.get(legacy_task=t)
        self.client.post(reverse('correspondence-delete', args=[corr.pk]))
        self.assertNotContains(self.client.get(reverse('admin-correspondence')), 'Legacy circular')
        self.assertFalse(Correspondence.objects.filter(title='Legacy circular').exists())

    def test_mirroring_twice_does_not_duplicate(self):
        t = Task.objects.create(title='Once', description='d', task_type='correspondence', created_by=self.mgr,
                                deadline=timezone.now() + timedelta(days=3))
        self.client.force_login(self.mgr)
        self.client.get(reverse('admin-correspondence'))
        self.client.get(reverse('admin-correspondence'))
        self.assertEqual(Correspondence.objects.filter(title='Once').count(), 1)


class ImpersonationReviewTests(TestCase):
    def test_cannot_impersonate_inactive_and_revert_needs_active_admin(self):
        admin = _u('a@t.local', 'super_admin')
        off = _u('off@t.local')
        off.is_active = False
        off.save()
        live = _u('live@t.local')
        self.client.force_login(admin)
        self.client.post(reverse('impersonate-user', args=[off.id]))
        self.assertEqual(int(self.client.session['_auth_user_id']), admin.id)
        self.client.post(reverse('impersonate-user', args=[live.id]))
        self.assertEqual(int(self.client.session['_auth_user_id']), live.id)
        admin.role = 'worker'
        admin.save()
        self.client.get(reverse('revert-impersonation'))
        self.assertNotIn('_auth_user_id', self.client.session)


class TasksApiTests(TestCase):
    def test_worker_can_read_assigned_but_not_write_tasks(self):
        mgr, w = _u('m@t.local', 'manager'), _u('w@t.local')
        t = Task.objects.create(title='Mine', description='d', created_by=mgr, deadline=timezone.now() + timedelta(days=2))
        t.assigned_to.add(w)
        c = APIClient()
        c.force_authenticate(w)
        self.assertEqual(c.get('/api/tasks/').status_code, 200)
        self.assertEqual(c.post('/api/tasks/', {'title': 'x', 'description': 'd'}, format='json').status_code, 403)
        self.assertEqual(c.patch(f'/api/tasks/{t.id}/', {'status': 'completed'}, format='json').status_code, 403)
        self.assertEqual(c.delete(f'/api/tasks/{t.id}/').status_code, 403)
        t.refresh_from_db()
        self.assertEqual(t.status, 'pending')
