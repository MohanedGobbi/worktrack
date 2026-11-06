import os
import django
import sys
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from tasks.models import Task
from submissions.models import Submission

tasks = Task.objects.all()
if not tasks.exists():
    print("No tasks found.")
else:
    t = tasks.first()
    s = t.submissions.first()
    print(f"Task: {t.title}, Current Progress: {t.progress}%")
    if s:
        print(f"Updating Submission {s.id} progress to 88%")
        s.progress = 88
        s.save()
        t.refresh_from_db()
        print(f"New Task Progress: {t.progress}%")
        if t.progress > 0:
             print("SUCCESS: Signal triggered recalculation.")
    else:
        # Create a dummy submission
        print("Creating dummy submission...")
        from users.models import CustomUser
        worker = t.assigned_to.first() or CustomUser.objects.filter(role='worker').first()
        if worker:
            s = Submission.objects.create(task=t, worker=worker, progress=75, status='submitted')
            t.refresh_from_db()
            print(f"New Task Progress after dummy sub: {t.progress}%")
            if t.progress > 0:
                print("SUCCESS: Signal triggered recalculation on create.")
            s.delete()
        else:
            print("No worker found to create submission.")
