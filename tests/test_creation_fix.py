from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser
from work_modules.models import WorkModule
from tasks.models import Task
import json

class TaskCreationFixTest(TestCase):
    def setUp(self):
        self.manager = CustomUser.objects.create_user(
            email='manager_fix@test.com', 
            password='TestPass123!',
            first_name='Fix',
            last_name='Manager',
            role='manager',
            username='manager_fix'
        )
        self.module = WorkModule.objects.create(name='Fix Module', slug='fix-module')
        self.client.force_login(self.manager)

    def test_ajax_task_creation_success(self):
        url = reverse('task-create')
        data = {
            'title': 'AJAX Task',
            'description': 'Test AJAX creation',
            'priority': 'medium',
            'task_type': 'task',
            'module': self.module.slug,
            'deadline': '2026-12-31',
            'estimated_hours': '10',
            'kpi_weight': '1.5'
        }
        # headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'} # In Django 4.0+ use headers
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        resp_data = response.json()
        self.assertEqual(resp_data['status'], 'success')
        self.assertIn('task_id', resp_data)
        self.assertTrue(Task.objects.filter(title='AJAX Task').exists())

    def test_ajax_task_creation_invalid_numeric(self):
        url = reverse('task-create')
        data = {
            'title': 'Invalid Numeric Task',
            'estimated_hours': 'not-a-number',
            'module': self.module.slug,
            'task_type': 'task',
            'priority': 'low',
            'deadline': '2026-12-31'
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 400)
        resp_data = response.json()
        self.assertEqual(resp_data['status'], 'error')
        self.assertIn('Invalid numeric value', resp_data['message'])

    def test_non_ajax_task_creation_invalid_numeric(self):
        url = reverse('task-create')
        data = {
            'title': 'Invalid Numeric Task Non-AJAX',
            'estimated_hours': 'not-a-number',
            'module': self.module.slug,
            'task_type': 'task',
            'priority': 'low',
            'deadline': '2026-12-31'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200) # Should re-render form
        self.assertContains(response, "Invalid numeric value")

    def test_task_form_renders_translatable_placeholders(self):
        response = self.client.get(reverse('task-create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'placeholder="Enter task title"')
        self.assertNotContains(response, 'placeholder="<span class="lang-en">')
