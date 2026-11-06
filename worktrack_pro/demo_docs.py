import os
import django
from django.core.files import File

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from tasks.models import Correspondence, CorrespondenceAttachment
from users.models import CustomUser

admin = CustomUser.objects.filter(is_superuser=True).first()

c = Correspondence.objects.create(
    title="Demo Multiple Files Test",
    description="Testing multiple file rendering with docx and txt together.",
    correspondence_type='memo',
    created_by=admin
)

# Open first file - text - attach as primary
with open('/app/media/demo_docs/sample.txt', 'rb') as f:
    c.attachment.save('sample.txt', File(f), save=True)
    
# Add docx attachment
ca = CorrespondenceAttachment(correspondence=c)
with open('/app/media/demo_docs/sample.docx', 'rb') as f:
    ca.file.save('sample.docx', File(f), save=True)

print(f"Created Correspondence #{c.id}")
