import os
import django
import datetime
from django.utils import timezone
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from work_modules.models import TemplateModule, TemplateTask, WorkModule
from tasks.models import Task
from users.models import CustomUser

def repro():
    user = CustomUser.objects.first()
    if not user:
        print("No user found")
        return

    # Create a template
    template = TemplateModule.objects.create(
        name=f"Template Correspondence Repro {int(datetime.datetime.now().timestamp())}",
        creator=user
    )

    # Create a template task with type correspondence
    t_task = TemplateTask.objects.create(
        template=template,
        title="Template Correspondence 1",
        description="Desc 1",
        task_type="correspondence",
        cover_image=None,
        attachment=SimpleUploadedFile("t_attach.pdf", b"fake_pdf_content", content_type="application/pdf")
    )
    print(f"Created TemplateTask {t_task.id} (type: correspondence) with NO cover and attachment: {t_task.attachment.name}")

    # Logic from module_create view
    module = WorkModule.objects.create(
        name=f"Module for Template {template.id}",
        slug=f"module-template-{template.id}-{int(datetime.datetime.now().timestamp())}",
        template=template
    )

    for tt in template.tasks.all():
        deadline = timezone.now() + datetime.timedelta(days=tt.deadline_offset_days)
        task = Task.objects.create(
            work_module=module,
            title=tt.title,
            description=tt.description,
            task_type=tt.task_type,
            created_by=user,
            deadline=deadline,
            priority=tt.priority,
            estimated_hours=tt.estimated_hours,
            kpi_weight=tt.kpi_weight,
            sequence_order=tt.sequence_order,
        )
        
        # COPY LOGIC (the one I implemented in module_create)
        if tt.cover_image:
            try:
                tt.cover_image.open('rb')
                task.cover_image.save(
                    os.path.basename(tt.cover_image.name), 
                    ContentFile(tt.cover_image.read()), 
                    save=False
                )
            finally:
                tt.cover_image.close()
        
        if tt.attachment:
            try:
                tt.attachment.open('rb')
                task.attachment.save(
                    os.path.basename(tt.attachment.name), 
                    ContentFile(tt.attachment.read()), 
                    save=False
                )
            finally:
                tt.attachment.close()
        task.save()
        print(f"Created Task {task.id} (type: {task.task_type}) from TemplateTask {tt.id}")

        # Verification
        if tt.cover_image:
            if task.cover_image and task.cover_image.name != tt.cover_image.name:
                print(f"✅ Cover image copied: {task.cover_image.name}")
            else:
                print(f"❌ Cover image NOT copied correctly: {task.cover_image.name if task.cover_image else 'None'}")
        
        if tt.attachment:
            if task.attachment and task.attachment.name != tt.attachment.name:
                print(f"✅ Attachment copied: {task.attachment.name}")
            else:
                print(f"❌ Attachment NOT copied correctly: {task.attachment.name if task.attachment else 'None'}")

if __name__ == "__main__":
    repro()
