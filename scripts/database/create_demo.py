import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from django.contrib.auth import get_user_model
from messaging.models import Conversation, ConversationMember, Message

User = get_user_model()
u1 = User.objects.filter(email='admin@example.com').first()
if not u1:
    u1 = User.objects.create_superuser('admin@example.com', 'admin')
u2 = User.objects.filter(email='user@example.com').first()
if not u2:
    u2 = User.objects.create_user(email='user@example.com', password='user')

conv = Conversation.objects.filter(is_group=False, members__user=u1).filter(members__user=u2).first()
if not conv:
    conv = Conversation.objects.create(is_group=False)
    ConversationMember.objects.create(user=u1, conversation=conv)
    ConversationMember.objects.create(user=u2, conversation=conv)

if not conv.messages.exists():
    Message.objects.create(sender=u2, conversation=conv, content='Hello from user!')

print("Demo data ready")
