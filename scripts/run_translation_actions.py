#!/usr/bin/env python3
import os
import sys
import django
import json
from types import SimpleNamespace

# Ensure project root is on sys.path so Django can import project packages
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from core.views_translations import api_manage_translations

for action in ('restore', 'deep_sync', 'dedupe'):
    user_obj = SimpleNamespace(role='super_admin', is_authenticated=True)
    req = SimpleNamespace(body=json.dumps({'action': action}).encode('utf-8'), user=user_obj, method='POST')
    print('\n===', action, '===')
    resp = api_manage_translations(req)
    try:
        print(resp.content.decode())
    except Exception:
        print(resp.content)
