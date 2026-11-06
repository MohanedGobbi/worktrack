import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from messaging.models import Message
try:
    msgs = reversed(Message.objects.all().order_by('-timestamp')[:20])
    for m in msgs:
        pass
    print("SUCCESS")
except Exception as e:
    print("EXCEPTION", repr(e))
