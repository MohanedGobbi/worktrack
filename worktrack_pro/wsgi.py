"""
WSGI config for worktrack_pro project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')

application = get_wsgi_application()
