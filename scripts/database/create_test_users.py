import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Department, UserProfile
from django.contrib.auth.hashers import make_password

User = get_user_model()

# Define users data
super_admins = [
    {"email": "admin@worktrack.com", "password": "Admin123!", "first_name": "Admin", "last_name": "User"},
    {"email": "superadmin@worktrack.com", "password": "SuperAdmin123!", "first_name": "Super", "last_name": "Admin"},
    {"email": "admin@admin.com", "password": "Admin123!", "first_name": "Default", "last_name": "Admin"},
]

managers = [
    {"email": "jane.smith@worktrack.com", "password": "Manager123!", "first_name": "Jane", "last_name": "Smith", "dept": "Sales"},
    {"email": "mike.johnson@worktrack.com", "password": "Manager123!", "first_name": "Mike", "last_name": "Johnson", "dept": "Finance"},
    {"email": "sarah.williams@worktrack.com", "password": "Manager123!", "first_name": "Sarah", "last_name": "Williams", "dept": "HR"},
]

workers = [
    {"email": "john.doe@worktrack.com", "password": "Worker123!", "first_name": "John", "last_name": "Doe", "dept": "Sales", "manager": "jane.smith@worktrack.com"},
    {"email": "emma.wilson@worktrack.com", "password": "Worker123!", "first_name": "Emma", "last_name": "Wilson", "dept": "Sales", "manager": "jane.smith@worktrack.com"},
    {"email": "alex.brown@worktrack.com", "password": "Worker123!", "first_name": "Alex", "last_name": "Brown", "dept": "Finance", "manager": "mike.johnson@worktrack.com"},
    {"email": "lisa.jones@worktrack.com", "password": "Worker123!", "first_name": "Lisa", "last_name": "Jones", "dept": "Finance", "manager": "mike.johnson@worktrack.com"},
    {"email": "david.taylor@worktrack.com", "password": "Worker123!", "first_name": "David", "last_name": "Taylor", "dept": "HR", "manager": "sarah.williams@worktrack.com"},
    {"email": "rachel.martin@worktrack.com", "password": "Worker123!", "first_name": "Rachel", "last_name": "Martin", "dept": "HR", "manager": "sarah.williams@worktrack.com"},
]

print("Starting test users creation...")

# 1. Create Super Admins
created_users = {}
for sa in super_admins:
    user, created = User.objects.get_or_create(email=sa["email"])
    user.username = sa["email"]
    user.first_name = sa["first_name"]
    user.last_name = sa["last_name"]
    user.password = make_password(sa["password"])
    user.role = "super_admin"
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
    user.save()
    created_users[sa["email"]] = user
    print(f"Super admin {sa['email']} is ready.")

# Use first superadmin as the owner/tenant admin
owner = created_users["admin@worktrack.com"]

# Set admin_owner for all super admins
for sa in super_admins:
    u = created_users[sa["email"]]
    u.admin_owner = owner
    u.save()

# 2. Create Managers and Departments
dept_objects = {}
for m in managers:
    # Create manager user
    user, created = User.objects.get_or_create(email=m["email"])
    user.username = m["email"]
    user.first_name = m["first_name"]
    user.last_name = m["last_name"]
    user.password = make_password(m["password"])
    user.role = "manager"
    user.is_superuser = False
    user.is_staff = True
    user.is_active = True
    user.admin_owner = owner
    user.save()
    created_users[m["email"]] = user
    
    # Create or update department
    dept, d_created = Department.objects.get_or_create(name=m["dept"])
    dept.manager = user
    dept.save()
    dept_objects[m["dept"]] = dept
    
    # Link manager to department
    user.department = dept
    user.save()
    print(f"Manager {m['email']} and Department {m['dept']} are ready.")

# 3. Create Workers
for w in workers:
    user, created = User.objects.get_or_create(email=w["email"])
    user.username = w["email"]
    user.first_name = w["first_name"]
    user.last_name = w["last_name"]
    user.password = make_password(w["password"])
    user.role = "worker"
    user.is_superuser = False
    user.is_staff = False
    user.is_active = True
    user.admin_owner = owner
    user.department = dept_objects[w["dept"]]
    user.save()
    created_users[w["email"]] = user
    
    # Set worker manager in profile
    profile = user.profile
    profile.manager = created_users[w["manager"]]
    profile.position = f"{w['dept']} Specialist"
    profile.save()
    print(f"Worker {w['email']} is ready (Manager: {w['manager']}).")

print("All test users and departments created successfully!")
