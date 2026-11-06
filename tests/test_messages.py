import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()
from messaging.models import Message, Conversation
print(f"Messages without conversation: {Message.objects.filter(conversation__isnull=True).count()}")
print(f"Messages with conversation: {Message.objects.filter(conversation__isnull=False).count()}")
