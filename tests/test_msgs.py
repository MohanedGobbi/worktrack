import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from django.contrib.auth import get_user_model
from messaging.models import Message, Conversation

User = get_user_model()
try:
    user = User.objects.first()
    conv = Conversation.objects.first()
    if not conv:
        conv = Conversation.objects.create(name='test')
    m = Message.objects.create(sender=user, conversation=conv, content='test message')
    qs = Message.objects.all().order_by('-timestamp')[:20]
    print("LEN:", len(qs))
    msgs = reversed(qs)
    for msg in msgs:
        pass
    print("FINISHED")
except Exception as e:
    import traceback
    traceback.print_exc()
