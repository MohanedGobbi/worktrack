import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from tasks.models import TaskTodo

print("All TaskTodos:", TaskTodo.objects.all().values('id', 'title', 'task__id'))
