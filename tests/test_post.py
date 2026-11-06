from django.test import Client
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "worktrack_pro.settings.base")
# Since the server might be running dev settings, let's just use the manage.py testing
