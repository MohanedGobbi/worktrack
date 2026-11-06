import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "worktrack_pro.settings")
django.setup()

from django.template.loader import render_to_string
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

rf = RequestFactory()
request = rf.get('/login/')
request.user = AnonymousUser()

try:
    print("Rendering...")
    render_to_string('auth/login.html', request=request)
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
