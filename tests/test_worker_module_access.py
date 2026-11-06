from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from users.models import CustomUser
from work_modules.models import WorkModule
from tasks.models import Task

def make_user(email, role='worker'):
    return CustomUser.objects.create_user(
        email=email, password='TestPass123!',
        first_name='Test', last_name=role.capitalize(),
        role=role, username=email,
    )

class WorkerModuleAccessTest(TestCase):
    def setUp(self):
        self.worker_assigned = make_user('worker1@test.com', 'worker')
        self.worker_unassigned = make_user('worker2@test.com', 'worker')
        self.manager = make_user('manager@test.com', 'manager')
        
        # Create a private module
        self.module = WorkModule.objects.create(
            name='Private Module',
            slug='private-module',
            is_private=True,
            is_shared=True,
            creator=self.manager
        )
        
        # Create a task assigned to worker1
        self.task = Task.objects.create(
            title='Assigned Task',
            description='Test Desc',
            work_module=self.module,
            created_by=self.manager,
            status='pending',
            deadline=timezone.now() + timezone.timedelta(days=7)
        )
        self.task.assigned_to.add(self.worker_assigned)

    def test_assigned_worker_can_access_module(self):
        self.client.force_login(self.worker_assigned)
        url = reverse('module-dashboard', args=[self.module.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.module.name)
        self.assertContains(response, self.task.title)

    def test_unassigned_worker_cannot_access_private_module(self):
        self.client.force_login(self.worker_unassigned)
        url = reverse('module-dashboard', args=[self.module.slug])
        response = self.client.get(url)
        # Should redirect to dashboard with error
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_worker_portal_shows_view_module_button(self):
        # We need to mock some context data if the view is complex, 
        # but let's see if the template renders the button
        self.client.force_login(self.worker_assigned)
        url = reverse('worker-portal')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check if the "Enter Dashboard" text is present
        self.assertContains(response, "Enter Dashboard")
        # Check if it links to the correct module
        module_url = reverse('module-dashboard', args=[self.module.slug])
        self.assertContains(response, module_url)
