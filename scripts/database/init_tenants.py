import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from users.models import CustomUser

super_admins = CustomUser.objects.filter(role='super_admin')
for sa in super_admins:
    sa.admin_owner = sa
    sa.save()

first_sa = super_admins.first()
if first_sa:
    CustomUser.objects.filter(admin_owner__isnull=True).update(admin_owner=first_sa)

print("Tenants initialized.")
