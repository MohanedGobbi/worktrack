import json
import tempfile
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from submissions.models import Submission
from tasks.models import Correspondence, Task

User = get_user_model()

DEMO = {
    'password': 'Demo-Pass-2026',
    'people': [
        {'email': 'boss@demo.local', 'first_name': 'B', 'role': 'manager', 'department': 'Office'},
        {'email': 'staff@demo.local', 'first_name': 'S', 'role': 'worker', 'department': 'Office', 'reports_to': 'boss@demo.local'},
    ],
    'groups': [{'slug': 'office', 'name': 'Office', 'members': ['boss@demo.local', 'staff@demo.local']}],
    'modules': [{'slug': 'reg', 'name': 'Registrations', 'owner': 'boss@demo.local', 'members': ['staff@demo.local']}],
    'tasks': [{'title': 'Check files', 'module': 'reg', 'created_by': 'boss@demo.local', 'assigned_to': ['staff@demo.local'],
               'submitted_by': 'staff@demo.local', 'status': 'submitted'}],
    'correspondence': [{'title': 'Circular 1', 'created_by': 'boss@demo.local', 'recipients': ['staff@demo.local']}],
}


class LoadDemoTests(TestCase):
    def _run(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'demo.json'
            p.write_text(json.dumps(DEMO), encoding='utf-8')
            call_command('load_demo', '--config', str(p), stdout=StringIO())

    @override_settings(DEBUG=True)
    def test_loads_and_is_rerunnable(self):
        self._run()
        self._run()
        self.assertEqual(User.objects.filter(email__endswith='@demo.local').count(), 2)
        staff = User.objects.get(email='staff@demo.local')
        self.assertTrue(staff.check_password('Demo-Pass-2026'))
        self.assertEqual(staff.profile.manager.email, 'boss@demo.local')
        self.assertEqual(Task.objects.get(title='Check files').work_module.slug, 'reg')
        self.assertEqual(Submission.objects.filter(status='submitted').count(), 1)
        self.assertEqual(Correspondence.objects.get(title='Circular 1').assigned_to.count(), 1)

    @override_settings(DEBUG=False)
    def test_refuses_without_debug(self):
        with self.assertRaises(CommandError):
            self._run()
