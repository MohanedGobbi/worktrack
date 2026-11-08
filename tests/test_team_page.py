from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from kpi.engine import KPICalculationEngine, month_scores
from kpi.models import KPIWeight
from submissions.models import Submission
from tasks.models import Task
from work_modules.models import WorkGroup, WorkModule

User = get_user_model()


def _u(email, role='worker', **kw):
    return User.objects.create_user(email=email, password='x', username=email, role=role, first_name=email.split('@')[0], **kw)


class TeamPageTests(TestCase):
    def setUp(self):
        self.admin = _u('admin@t.local', 'super_admin')
        self.mgr = _u('mgr@t.local', 'manager')
        self.w1, self.w2, self.stranger = _u('w1@t.local'), _u('w2@t.local'), _u('stranger@t.local')
        g = WorkGroup.objects.create(name='Team', slug='team')
        for u in (self.mgr, self.w1, self.w2):
            g.members.add(u)
        self.module = WorkModule.objects.create(name='Ops', slug='ops', creator=self.mgr)
        now = timezone.now()
        self.task = Task.objects.create(title='Report', description='d', created_by=self.mgr, deadline=now + timedelta(days=2), work_module=self.module)
        self.task.assigned_to.add(self.w1)
        self.late = Task.objects.create(title='Late one', description='d', created_by=self.mgr, deadline=now - timedelta(days=2), work_module=self.module)
        self.late.assigned_to.add(self.w1)
        self.sub = Submission.objects.create(task=self.task, worker=self.w1, status='submitted', submitted_at=now)

    def test_bulk_scores_match_the_engine(self):
        now = timezone.now()
        Submission.objects.create(task=self.late, worker=self.w1, status='approved', score=80, submitted_at=now, reviewed_at=now)
        Submission.objects.create(task=self.task, worker=self.w2, status='rejected', score=40, submitted_at=now, reviewed_at=now)
        weights = KPIWeight.get_weights()
        bulk = month_scores([self.w1, self.w2, self.stranger], now.date(), weights)
        for u in (self.w1, self.w2, self.stranger):
            engine = KPICalculationEngine(u, now)
            self.assertAlmostEqual(bulk[u.id]['total'], engine.calculate_total_score(), places=6, msg=u.email)
            self.assertAlmostEqual(bulk[u.id]['quality'], engine.calculate_quality_score(), places=6)

    def test_manager_sees_team_review_queue_and_overdue(self):
        self.client.force_login(self.mgr)
        r = self.client.get(reverse('manager-analytics'))
        self.assertContains(r, 'Report')
        self.assertContains(r, 'w1')
        self.assertNotContains(r, 'stranger@t.local')
        self.assertEqual(r.context['overdue_total'], 1)
        self.assertEqual(r.context['review_count'], 1)

    def test_workers_are_turned_away_and_old_pages_redirect(self):
        self.client.force_login(self.w1)
        self.assertEqual(self.client.get(reverse('manager-analytics')).status_code, 302)
        self.client.force_login(self.mgr)
        for name in ('manager-portal', 'kpi-dashboard'):
            r = self.client.get(reverse(name))
            self.assertRedirects(r, reverse('manager-analytics'), fetch_redirect_response=False)

    def test_admin_sees_everyone(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('manager-analytics'))
        self.assertContains(r, 'stranger')
        self.assertEqual(r.context['team_total'], 4)  # 3 staff + the manager
