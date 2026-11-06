import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from messaging.models import Conversation, Message
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()
try:
    user = User.objects.first()
    conv = Conversation.objects.first()
    if not conv:
        conv = Conversation.objects.create(name='test')
        m = Message.objects.create(sender=user, conversation=conv, content='test 1')
        m = Message.objects.create(sender=user, conversation=conv, content='test 2')
    
    print("Messages in DB for conv:", conv.messages.count())
    
    c = Client()
    c.force_login(user)
    resp = c.get(f'/messaging/api/messages/conv/{conv.id}/?offset=0')
    print("API STATUS:", resp.status_code)
    print("API RESPONSE:", resp.json())
except Exception as e:
    import traceback
    traceback.print_exc()
