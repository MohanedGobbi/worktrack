from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notifications.models import Notification
from users.models import UserProfile

User = get_user_model()


def _user(email, role='worker', **kw):
    return User.objects.create_user(email=email, password='Old-pass-123!', username=email, role=role, first_name='A', **kw)


class NotificationsPageTests(TestCase):
    def setUp(self):
        self.u = _user('n@t.local')
        self.other = _user('o@t.local')
        self.client.force_login(self.u)
        self.a = Notification.objects.create(recipient=self.u, notification_type='task_assigned', title='Task one', message='m',
                                             related_object_type='task', related_object_id=7)
        self.b = Notification.objects.create(recipient=self.u, notification_type='submission_approved', title='Approved', message='m')
        self.x = Notification.objects.create(recipient=self.other, notification_type='task_assigned', title='Not mine', message='m')

    def test_list_groups_links_and_filters(self):
        r = self.client.get(reverse('notifications-list'))
        self.assertContains(r, 'Task one')
        self.assertContains(r, reverse('task-detail', args=[7]))
        self.assertNotContains(r, 'Not mine')
        r = self.client.get(reverse('notifications-list'), {'type': 'submission_approved'})
        self.assertContains(r, 'Approved')
        self.assertNotContains(r, 'Task one')

    def test_ajax_read_and_delete(self):
        url = reverse('notification-mark-as-read', args=[self.a.id])
        r = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.json()['unread_count'], 1)
        self.a.refresh_from_db()
        self.assertTrue(self.a.is_read and self.a.read_at)
        r = self.client.post(reverse('notification-delete', args=[self.b.id]), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Notification.objects.filter(id=self.b.id).exists())

    def test_cannot_touch_someone_elses(self):
        r = self.client.post(reverse('notification-delete', args=[self.x.id]))
        self.assertEqual(r.status_code, 404)


class ProfilePageTests(TestCase):
    def setUp(self):
        self.u = _user('p@t.local')
        self.client.force_login(self.u)

    def test_details_saved_and_shown(self):
        self.client.post(reverse('profile-update'), {'first_name': 'Sara', 'last_name': 'B', 'position': 'Clerk', 'phone': '+213 5', 'bio': 'Hi'})
        prof = UserProfile.objects.get(user=self.u)
        self.assertEqual((prof.position, prof.phone, prof.bio), ('Clerk', '+213 5', 'Hi'))
        r = self.client.get(reverse('profile'))
        self.assertContains(r, 'value="+213 5"')
        self.assertContains(r, 'Clerk')

    def test_password_change_keeps_session(self):
        r = self.client.post(reverse('profile-change-password'), {'current_password': 'Old-pass-123!', 'new_password1': 'Brand-new-pass-9', 'new_password2': 'Brand-new-pass-9'})
        self.assertEqual(r.status_code, 302)
        self.u.refresh_from_db()
        self.assertTrue(self.u.check_password('Brand-new-pass-9'))
        self.assertEqual(self.client.get(reverse('profile')).status_code, 200)  # still signed in

    def test_weak_password_rejected(self):
        self.client.post(reverse('profile-change-password'), {'current_password': 'Old-pass-123!', 'new_password1': '12345678', 'new_password2': '12345678'})
        self.u.refresh_from_db()
        self.assertTrue(self.u.check_password('Old-pass-123!'))
        self.assertContains(self.client.get(reverse('profile')), 'is-invalid')


class ScorePageTests(TestCase):
    def test_own_score_renders(self):
        u = _user('s@t.local')
        self.client.force_login(u)
        r = self.client.get(reverse('worker-performance'))
        self.assertContains(r, 'wt-ks-parts')
        self.assertEqual(len(r.context['history']), 6)

    def test_worker_cannot_open_someone_else(self):
        u = _user('w1@t.local'); other = _user('w2@t.local', last_name='Other')
        self.client.force_login(u)
        r = self.client.get(reverse('worker-performance'), {'user_id': other.id})
        self.assertEqual(r.context['target_user'], u)

    def test_manager_limited_to_team(self):
        mgr = _user('m@t.local', role='manager')
        stranger = _user('x@t.local')
        self.client.force_login(mgr)
        r = self.client.get(reverse('worker-performance'), {'user_id': stranger.id})
        self.assertEqual(r.status_code, 404)

    def test_admin_can_open_anyone(self):
        admin = _user('a@t.local', role='super_admin')
        w = _user('w3@t.local')
        self.client.force_login(admin)
        r = self.client.get(reverse('worker-performance'), {'user_id': w.id})
        self.assertEqual(r.context['target_user'], w)
