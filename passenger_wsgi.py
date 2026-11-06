import os
import sys

# cPanel passenger root directory injection
sys.path.insert(0, os.path.dirname(__file__))

# Setup environment for decoupling or basic Django configuration
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')

# Import the WSGI application from your Django project
from worktrack_pro.wsgi import application

