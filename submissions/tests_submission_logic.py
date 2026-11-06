from django.test import TestCase
from django.contrib.auth import get_user_model
from tasks.models import Task
from submissions.models import Submission
from django.utils import timezone

User = get_user_model()

class SubmissionMatrixTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(email='manager@test.com', password='password', role='manager')
        self.worker1 = User.objects.create_user(email='worker1@test.com', password='password', role='worker', first_name='Adam')
        self.worker2 = User.objects.create_user(email='worker2@test.com', password='password', role='worker', first_name='Zoe')
        
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            created_by=self.manager,
            deadline=timezone.now() + timezone.timedelta(days=1)
        )
        self.task.assigned_to.add(self.worker1, self.worker2)

    def test_latest_submission_filtering(self):
        # Create multiple versions for worker1
        Submission.objects.create(task=self.task, worker=self.worker1, version=1, status='submitted')
        sub1_v2 = Submission.objects.create(task=self.task, worker=self.worker1, version=2, status='submitted')
        
        # Create one version for worker2
        sub2_v1 = Submission.objects.create(task=self.task, worker=self.worker2, version=1, status='submitted')
        
        # Logic from core/template_views.py
        all_subs_queryset = Submission.objects.filter(task=self.task).prefetch_related(
            'field_values__field', 'worker'
        ).order_by('worker__id', '-version')

        latest_subs = {}
        for sub in all_subs_queryset:
            if sub.worker_id not in latest_subs:
                latest_subs[sub.worker_id] = sub
        
        all_subs = sorted(latest_subs.values(), key=lambda s: s.worker.get_full_name() or s.worker.email)
        
        # Assertions
        self.assertEqual(len(all_subs), 2)
        self.assertIn(sub1_v2, all_subs)
        self.assertIn(sub2_v1, all_subs)
        
        # Check that older versions are NOT in the list
        sub1_v1 = Submission.objects.filter(task=self.task, worker=self.worker1, version=1).first()
        self.assertNotIn(sub1_v1, all_subs)
        
        # Verify ordering (Adam before Zoe)
        self.assertEqual(all_subs[0].worker, self.worker1)
        self.assertEqual(all_subs[1].worker, self.worker2)
