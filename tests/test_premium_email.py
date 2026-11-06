import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

from core.email_notifications import render_premium_email
from django.contrib.auth import get_user_model
from notifications.models import EmailTemplate, EmailStyle

User = get_user_model()

def test_rendering():
    # 1. Get or create a test user
    user, created = User.objects.get_or_create(
        email='test_notifier@example.com',
        defaults={'first_name': 'Test', 'last_name': 'User', 'username': 'testuser_notifier'}
    )
    
    # 2. Ensure we have templates and styles
    style = EmailStyle.objects.first()
    if not style:
        style = EmailStyle.objects.create(company_name='WorkTrack Pro Test', primary_color='#2563eb')
        print('Created test style')
    
    n_type = 'task_assigned'
    template, created = EmailTemplate.objects.get_or_create(
        notification_type=n_type,
        defaults={
            'subject': 'New Task: {title}',
            'body': 'Hello {recipient_name}, you have a new task: <b>{title}</b>.'
        }
    )
    if created:
        print(f'Created template for {n_type}')
    
    # 3. Render
    subject, html = render_premium_email(n_type, 'Finish the Report', 'Go to dashboard', user)
    
    print(f'--- SUBJECT ---\n{subject}')
    print(f'--- STYLE ---\nPrimary: {style.primary_color}')
    
    if 'WorkTrack Pro' in html and 'Finish the Report' in html and 'Test User' in html:
        print('\n✅ Verification Successful: Placeholders and styling applied.')
    else:
        print('\n❌ Verification Failed: Some elements missing.')

if __name__ == '__main__':
    test_rendering()
