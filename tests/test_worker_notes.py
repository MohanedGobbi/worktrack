"""Workers keep personal notes in the shell drawer; module to-dos stay with managers."""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from users.models import CustomUser
from tasks.models import Todo
from work_modules.models import WorkModule


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class WorkerNotesTests(TestCase):
    def setUp(self):
        settings.ALLOWED_HOSTS = ['*']
        self.worker = CustomUser.objects.create_user(email='w@test.com', username='w@test.com', password='TestPass123!', role='worker')
        self.other = CustomUser.objects.create_user(email='o@test.com', username='o@test.com', password='TestPass123!', role='worker')
        self.manager = CustomUser.objects.create_user(email='m@test.com', username='m@test.com', password='TestPass123!', role='manager')
        self.module = WorkModule.objects.create(name='Mod', slug='mod', creator=self.manager)
        self.c = Client(HTTP_HOST='127.0.0.1')
        self.c.force_login(self.worker)

    def test_worker_adds_lists_toggles_and_deletes_own_note(self):
        r = self.c.post(reverse('module-todo-add', args=['general']), {'title': 'Call the lab', 'priority': 'medium'})
        self.assertEqual(r.json()['status'], 'success')
        todo_id = r.json()['todo']['id']
        listed = self.c.get(reverse('module-todo-list-ajax', args=['all'])).json()['todos']
        self.assertEqual([t['id'] for t in listed], [todo_id])
        self.assertEqual(self.c.post(reverse('module-todo-toggle', args=[todo_id])).json()['new_status'], 'completed')
        self.assertEqual(self.c.post(reverse('module-todo-delete', args=[todo_id])).json()['status'], 'success')

    def test_worker_cannot_add_module_todo(self):
        r = self.c.post(reverse('module-todo-add', args=[self.module.slug]), {'title': 'x'})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.c.get(reverse('module-todo-list-ajax', args=[self.module.slug])).status_code, 403)

    def test_worker_cannot_touch_someone_elses_note(self):
        theirs = Todo.objects.create(title='private', created_by=self.other, status='pending')
        for name in ('module-todo-toggle', 'module-todo-delete', 'module-todo-update'):
            self.assertEqual(self.c.post(reverse(name, args=[theirs.id]), {'title': 'hacked'}).status_code, 403, name)
        self.assertTrue(Todo.objects.filter(id=theirs.id, title='private', status='pending').exists())

    def test_manager_module_todos_unchanged(self):
        c = Client(HTTP_HOST='127.0.0.1')
        c.force_login(self.manager)
        r = c.post(reverse('module-todo-add', args=[self.module.slug]), {'title': 'Module item'})
        self.assertEqual(r.json()['status'], 'success')
