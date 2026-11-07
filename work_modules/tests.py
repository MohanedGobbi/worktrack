import unittest
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
User = get_user_model()
from work_modules.models import WorkModule
from tasks.models import Task

class ModuleEnrollmentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.worker = User.objects.create_user(
            username='worker1', email='worker1@example.com', password='password123', role='worker'
        )
        self.admin = User.objects.create_user(
            username='admin1', email='admin1@example.com', password='password123', role='super_admin'
        )
        
        # Open module
        self.module_open = WorkModule.objects.create(
            name='Open Module', slug='open-module', creator=self.admin, allow_enrollment=True
        )
        from django.utils import timezone
        self.task1 = Task.objects.create(
            work_module=self.module_open, title='Task 1', created_by=self.admin, task_type='standard', deadline=timezone.now()
        )
        
        # Closed module
        self.module_closed = WorkModule.objects.create(
            name='Closed Module', slug='closed-module', creator=self.admin, allow_enrollment=False
        )

    def test_available_modules_view(self):
        self.client.login(email='worker1@example.com', password='password123')
        response = self.client.get(reverse('available-modules'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Open Module')
        self.assertNotContains(response, 'Closed Module')

    def test_enroll_action(self):
        self.client.login(email='worker1@example.com', password='password123')
        response = self.client.post(reverse('enroll-module', args=[self.module_open.slug]))
        
        # Verify redirect to module dashboard
        self.assertRedirects(response, reverse('module-dashboard', args=[self.module_open.slug]))
        
        # Verify assignment
        self.assertTrue(self.task1.assigned_to.filter(id=self.worker.id).exists())
        
        # Ensure it no longer appears in available since they are enrolled
        response2 = self.client.get(reverse('available-modules'))
        self.assertNotIn(self.module_open, response2.context['modules'])

    @unittest.skip('Sidebar module paging is not part of the rebuilt shell (no template renders it).')
    def test_sidebar_renders_paginated_module_groups(self):
        self.client.login(email='admin1@example.com', password='password123')
        for index in range(6):
            WorkModule.objects.create(name=f'Paginated Module {index}', slug=f'paginated-module-{index}', creator=self.admin)

        request = RequestFactory().get('/')
        request.user = self.admin
        request.session = {}

        html = render_to_string('includes/sidebar.html', {
            'all_modules_list': WorkModule.get_visible_modules(self.admin),
            'module_pages': [list(WorkModule.get_visible_modules(self.admin)[:5]), list(WorkModule.get_visible_modules(self.admin)[5:])],
            'user': self.admin,
            'request': request,
        })

        self.assertIn('page-1', html)
        self.assertIn('Page 1', html)
        self.assertIn('data-sidebar-page-btn="1"', html)
        self.assertIn('data-sidebar-module-page="1"', html)

