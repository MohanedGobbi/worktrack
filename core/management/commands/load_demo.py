"""Load demo people and sample work from a JSON file, for local testing only.

    manage.py load_demo --config institutions/<name>/demo.json

Refuses to run unless DEBUG=True: the accounts have known passwords. Safe to re-run: people are matched by email
(password and details are reset), groups and modules by slug, tasks and circulars by title.

JSON keys (all optional except people):
  password            shared password for every demo account
  people              [{email, first_name, last_name, role, department, profile, reports_to, groups: [slug]}]
  groups              [{slug, name, members: [email]}]
  modules             [{slug, name, description, color, owner, members: [email]}]
  tasks               [{title, description, module, created_by, assigned_to: [email], priority, status,
                        progress, due_in_days, submitted_by (creates a submission waiting for review)}]
  correspondence      [{title, description, type, reference, priority, created_by, recipients: [email], due_in_days}]
"""
import json
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Load demo accounts and sample work from a JSON file (DEBUG only).'

    def add_arguments(self, parser):
        parser.add_argument('--config', required=True, help='Path to the demo JSON file.')

    def handle(self, *args, **opts):
        if not settings.DEBUG:
            raise CommandError('load_demo only runs with DEBUG=True: demo accounts have known passwords.')
        path = Path(opts['config'])
        if not path.is_file():
            raise CommandError(f'Demo file not found: {path}')
        data = json.loads(path.read_text(encoding='utf-8'))
        with transaction.atomic():
            people = self._people(data)
            self._groups(data, people)
            modules = self._modules(data, people)
            self._tasks(data, people, modules)
            self._correspondence(data, people)
        self.stdout.write(self.style.SUCCESS(f'Demo loaded: {len(people)} accounts.'))
        for email, u in people.items():
            self.stdout.write(f'  {email:<38} {u.role:<12} {data.get("password", "")}')

    def _people(self, data):
        from users.models import CustomUser, Department, SystemProfile, UserProfile
        password = data.get('password') or 'Demo-2026-pass'
        people = {}
        for p in data.get('people', []):
            email = p['email'].strip().lower()
            u = CustomUser.objects.filter(email__iexact=email).first() or CustomUser(email=email, username=email[:150])
            u.first_name, u.last_name = p.get('first_name', ''), p.get('last_name', '')
            u.role = p.get('role', 'worker')
            u.is_superuser = u.is_staff = u.role == 'super_admin'
            u.is_active = True
            if p.get('department'):
                u.department, _ = Department.objects.get_or_create(name=p['department'])
            u.set_password(password)
            u.save()
            if p.get('profile'):
                profile = SystemProfile.objects.filter(name=p['profile']).first()
                if profile:
                    u.system_profiles.add(profile)
            people[email] = u
        for p in data.get('people', []):
            if p.get('reports_to'):
                prof, _ = UserProfile.objects.get_or_create(user=people[p['email'].lower()])
                prof.manager = people.get(p['reports_to'].lower())
                prof.position = p.get('position', prof.position)
                prof.save()
        return people

    def _groups(self, data, people):
        from work_modules.models import WorkGroup
        for g in data.get('groups', []):
            group, _ = WorkGroup.objects.get_or_create(slug=g['slug'], defaults={'name': g['name']})
            group.name = g['name']
            group.save()
            group.members.add(*[people[e.lower()] for e in g.get('members', []) if e.lower() in people])

    def _modules(self, data, people):
        from work_modules.models import WorkModule
        modules = {}
        for m in data.get('modules', []):
            mod, _ = WorkModule.objects.get_or_create(slug=m['slug'], defaults={'name': m['name']})
            mod.name, mod.description = m['name'], m.get('description', '')
            mod.color = m.get('color', mod.color)
            mod.creator = people.get((m.get('owner') or '').lower(), mod.creator)
            mod.save()
            if hasattr(mod, 'enrolled_users'):
                mod.enrolled_users.add(*[people[e.lower()] for e in m.get('members', []) if e.lower() in people])
            modules[m['slug']] = mod
        return modules

    def _tasks(self, data, people, modules):
        from submissions.models import Submission
        from tasks.models import Task
        now = timezone.now()
        for t in data.get('tasks', []):
            creator = people[t['created_by'].lower()]
            task, _ = Task.objects.get_or_create(title=t['title'], defaults={
                'description': t.get('description', ''), 'created_by': creator,
                'deadline': now + timedelta(days=t.get('due_in_days', 7))})
            task.description = t.get('description', task.description)
            task.work_module = modules.get(t.get('module'))
            task.priority = t.get('priority', 'medium')
            task.status = t.get('status', 'pending')
            task.progress = t.get('progress', 0)
            task.deadline = now + timedelta(days=t.get('due_in_days', 7))
            task.save()
            task.assigned_to.set([people[e.lower()] for e in t.get('assigned_to', []) if e.lower() in people])
            if t.get('submitted_by'):
                worker = people[t['submitted_by'].lower()]
                Submission.objects.get_or_create(task=task, worker=worker, defaults={
                    'status': 'submitted', 'notes': t.get('submission_notes', ''), 'submitted_at': now})

    def _correspondence(self, data, people):
        from tasks.models import Correspondence
        now = timezone.now()
        for c in data.get('correspondence', []):
            corr, _ = Correspondence.objects.get_or_create(title=c['title'], defaults={
                'created_by': people[c['created_by'].lower()]})
            corr.description = c.get('description', '')
            corr.correspondence_type = c.get('type', 'circular')
            corr.reference_number = c.get('reference') or None
            corr.priority = c.get('priority', 'medium')
            corr.deadline = now + timedelta(days=c['due_in_days']) if c.get('due_in_days') else None
            corr.status = 'active'
            corr.save()
            corr.assigned_to.set([people[e.lower()] for e in c.get('recipients', []) if e.lower() in people])
