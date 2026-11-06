import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "worktrack_pro.settings")
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.filter(role='super_admin').first()
c = Client()
c.force_login(u)
res = c.get('/dashboard/')
with open('rendered_output.html', 'wb') as f:
    f.write(res.content)
print("Done")
