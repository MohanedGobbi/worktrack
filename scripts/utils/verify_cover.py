import os
import sys
import django
from django.core.files.uploadedfile import SimpleUploadedFile
from setuptools import setup, find_packages
from PIL import Image

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from tasks.models import Task
from users.models import CustomUser

# Create a test PDF
from reportlab.pdfgen import canvas
pdf_path = '/tmp/test_doc.pdf'
c = canvas.Canvas(pdf_path)
c.drawString(100, 750, "Test Correspondence Document")
c.save()

try:
    admin_user = CustomUser.objects.filter(role__in=['super_admin', 'manager']).first()
    
    with open(pdf_path, 'rb') as f:
        pdf_file = SimpleUploadedFile("test_doc.pdf", f.read(), content_type="application/pdf")
        
    task = Task.objects.create(
        title="Automated Test Correspondence",
        description="Testing thumbnail generation",
        task_type="correspondence",
        created_by=admin_user,
        attachment=pdf_file,
        deadline="2026-12-31T23:59:59Z"
    )

    print(f"Task created: {task.id}")
    if task.cover_image:
        print(f"Success! Cover image generated: {task.cover_image.url}")
    else:
        print("Failed! No cover image generated.")
except Exception as e:
    print(f"Error: {e}")
