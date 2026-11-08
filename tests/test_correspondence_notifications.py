from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

from users.models import CustomUser
from work_modules.models import WorkModule
from tasks.models import Correspondence
from notifications.models import Notification

def make_user(email, role='worker', password='TestPass123!'):
    return CustomUser.objects.create_user(
        email=email, password=password,
        first_name='Test', last_name=role.capitalize(),
        role=role, username=email,
    )

class CorrespondenceNotificationTest(TestCase):
    def setUp(self):
        self.manager = make_user('manager_corr@test.com', 'manager')
        self.worker1 = make_user('worker_corr1@test.com', 'worker')
        self.worker2 = make_user('worker_corr2@test.com', 'worker')
        self.module  = WorkModule.objects.create(name='Corr Module', slug='corr-module', creator=self.manager)
        # Recipients must be people the manager works with (a shared group), as the form's picker offers.
        from work_modules.models import WorkGroup
        group = WorkGroup.objects.create(name='Corr Team', slug='corr-team')
        for person in (self.manager, self.worker1, self.worker2):
            group.members.add(person)
        self.client.force_login(self.manager)

    def test_notification_on_correspondence_create(self):
        """Test that notifications are created when a correspondence is created and assigned."""
        url = reverse('correspondence-create')
        data = {
            'title': 'Official Directive #1',
            'description': 'Please follow these instructions.',
            'correspondence_type': 'directive',
            'priority': 'high',
            'deadline': (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'work_module': self.module.id,
            'assigned_to': [self.worker1.id, self.worker2.id],
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302) # Redirect to detail page
        
        # Check Correspondence count
        self.assertEqual(Correspondence.objects.count(), 1)
        corr = Correspondence.objects.first()
        
        # Check Notification count
        # Expect 2 notifications (one for each worker)
        notifications = Notification.objects.filter(notification_type='correspondence_issued')
        self.assertEqual(notifications.count(), 2)
        
        recipient_emails = set(n.recipient.email for n in notifications)
        self.assertIn(self.worker1.email, recipient_emails)
        self.assertIn(self.worker2.email, recipient_emails)
        
        for n in notifications:
            self.assertIn('Official Directive #1', n.title)
            self.assertEqual(n.related_object_type, 'correspondence')
            self.assertEqual(n.related_object_id, corr.id)

    def test_notification_on_correspondence_edit(self):
        """Test that notifications are created for NEWLY assigned workers on edit."""
        corr = Correspondence.objects.create(
            title='Initial Title',
            created_by=self.manager,
            work_module=self.module,
            status='active'
        )
        corr.assigned_to.add(self.worker1)
        
        # Initial notifications (none yet because we created directly)
        self.assertEqual(Notification.objects.count(), 0)
        
        url = reverse('correspondence-edit', args=[corr.id])
        data = {
            'title': 'Updated Title',
            'assigned_to': [self.worker1.id, self.worker2.id], # Added worker2
            'status': 'active',
            'correspondence_type': 'memo',
            'priority': 'medium'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Should only notify worker2 because worker1 was already assigned
        notifications = Notification.objects.filter(recipient=self.worker2)
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications[0].notification_type, 'correspondence_issued')
        
        # Worker1 should NOT have a new notification from this edit
        worker1_notifications = Notification.objects.filter(recipient=self.worker1)
        self.assertEqual(worker1_notifications.count(), 0)
