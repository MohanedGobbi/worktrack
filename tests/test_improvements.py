"""
Automated Tests for Worktrack Pro — Improvement #20
Tests cover: task assignment, submission workflow, permission checks, task comments, global search, deadline enforcement.
Run with: python manage.py test tests.test_improvements -v2
"""
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

from users.models import CustomUser
from work_modules.models import WorkModule
from tasks.models import Task, TaskComment
from submissions.models import Submission


def make_user(email, role='worker', password='TestPass123!'):
    return CustomUser.objects.create_user(
        email=email, password=password,
        first_name='Test', last_name=role.capitalize(),
        role=role, username=email,
    )


class TaskCreationTest(TestCase):
    def setUp(self):
        self.manager = make_user('manager@test.com', 'manager')
        self.worker  = make_user('worker@test.com',  'worker')
        self.module  = WorkModule.objects.create(name='Test Module', slug='test-module')

    def test_manager_can_create_task(self):
        task = Task.objects.create(
            title='Test Task', description='Desc',
            deadline=timezone.now() + timedelta(days=7),
            created_by=self.manager, work_module=self.module,
        )
        task.assigned_to.add(self.worker)
        self.assertEqual(Task.objects.count(), 1)
        self.assertIn(self.worker, task.assigned_to.all())

    def test_task_overdue_property(self):
        task = Task(
            title='Old Task', description='desc',
            deadline=timezone.now() - timedelta(hours=1),
            status='pending', created_by=self.manager,
        )
        self.assertTrue(task.is_overdue)

    def test_task_not_overdue_when_approved(self):
        task = Task(
            title='Approved Task', description='desc',
            deadline=timezone.now() - timedelta(hours=1),
            status='approved', created_by=self.manager,
        )
        self.assertFalse(task.is_overdue)


class SubmissionWorkflowTest(TestCase):
    def setUp(self):
        self.manager = make_user('manager2@test.com', 'manager')
        self.worker  = make_user('worker2@test.com',  'worker')
        self.task = Task.objects.create(
            title='WF Task', description='desc',
            deadline=timezone.now() + timedelta(days=3),
            created_by=self.manager, status='pending',
        )
        self.task.assigned_to.add(self.worker)

    def test_submission_created_as_draft(self):
        sub = Submission.objects.create(
            task=self.task, worker=self.worker, notes='My work', status='draft',
        )
        self.assertEqual(sub.status, 'draft')
        self.assertEqual(sub.version, 1)

    def test_submission_can_be_approved(self):
        sub = Submission.objects.create(
            task=self.task, worker=self.worker, notes='Done', status='submitted',
            submitted_at=timezone.now(),
        )
        sub.status = 'approved'
        sub.score = 90
        sub.reviewed_by = self.manager
        sub.reviewed_at = timezone.now()
        sub.save()
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'approved')
        self.assertEqual(sub.score, 90)


class PermissionTest(TestCase):
    def setUp(self):
        self.worker = make_user('worker3@test.com', 'worker')

    def test_worker_cannot_access_analytics(self):
        self.client.force_login(self.worker)
        resp = self.client.get(reverse('manager-analytics'))
        self.assertIn(resp.status_code, [302, 403])

    def test_unauthenticated_redirected_to_login(self):
        resp = self.client.get(reverse('task-list'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])


class TaskCommentTest(TestCase):
    def setUp(self):
        self.manager = make_user('mgr4@test.com', 'manager')
        self.worker  = make_user('wrk4@test.com',  'worker')
        self.task = Task.objects.create(
            title='Comment Task', description='desc',
            deadline=timezone.now() + timedelta(days=5),
            created_by=self.manager,
        )
        self.task.assigned_to.add(self.worker)

    def test_worker_can_post_comment(self):
        self.client.force_login(self.worker)
        resp = self.client.post(
            reverse('task-comment-add', args=[self.task.id]),
            data={'message': 'Hello, I have a question about this task.'},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('id', data)
        self.assertEqual(TaskComment.objects.count(), 1)

    def test_empty_comment_rejected(self):
        self.client.force_login(self.worker)
        resp = self.client.post(
            reverse('task-comment-add', args=[self.task.id]),
            data={'message': ''},
        )
        self.assertEqual(resp.status_code, 400)

    def test_outsider_cannot_comment(self):
        outsider = make_user('outsider@test.com', 'worker')
        self.client.force_login(outsider)
        resp = self.client.post(
            reverse('task-comment-add', args=[self.task.id]),
            data={'message': 'Sneaky comment'},
        )
        self.assertEqual(resp.status_code, 403)


class GlobalSearchTest(TestCase):
    def setUp(self):
        self.admin   = make_user('admin5@test.com', 'super_admin')
        self.manager = make_user('mgr5@test.com',   'manager')
        self.task = Task.objects.create(
            title='Budget Planning Report', description='Finance',
            deadline=timezone.now() + timedelta(days=10),
            created_by=self.manager,
        )
        self.task.assigned_to.add(self.manager)

    def test_search_finds_task_by_title(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('global-search'), {'q': 'Budget'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreater(len(data['tasks']), 0)
        self.assertEqual(data['tasks'][0]['title'], 'Budget Planning Report')

    def test_short_query_returns_empty(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('global-search'), {'q': 'B'})
        data = resp.json()
        self.assertEqual(data['tasks'], [])


class DeadlineCommandTest(TestCase):
    def setUp(self):
        self.manager = make_user('mgr6@test.com', 'manager')
        self.worker  = make_user('wrk6@test.com', 'worker')

    def test_check_deadlines_marks_overdue(self):
        from django.core.management import call_command
        task = Task.objects.create(
            title='Overdue task', description='old',
            deadline=timezone.now() - timedelta(hours=2),
            status='pending', created_by=self.manager,
        )
        task.assigned_to.add(self.worker)
        call_command('check_deadlines', verbosity=0)
        task.refresh_from_db()
        self.assertEqual(task.status, 'overdue')

    def test_approved_task_not_overdue_after_command(self):
        from django.core.management import call_command
        task = Task.objects.create(
            title='Approved old task', description='done',
            deadline=timezone.now() - timedelta(hours=2),
            status='approved', created_by=self.manager,
        )
        call_command('check_deadlines', verbosity=0)
        task.refresh_from_db()
        self.assertEqual(task.status, 'approved')  # Should not be changed


