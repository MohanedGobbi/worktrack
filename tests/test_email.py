import os
import sys
import django
from django.core.mail import send_mail
from django.conf import settings

from pathlib import Path

# Setup Django environment dynamically
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'worktrack_pro'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktrack_pro.settings')
django.setup()

def test_smtp():
    print("--- SMTP Diagnostic Tool ---")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    recipient = input("Enter recipient email address to test: ")
    if not recipient:
        print("No recipient provided. Exiting.")
        return

    print(f"\nAttempting to send a test email to {recipient}...")
    try:
        send_mail(
            subject='[WorkTrack Pro] SMTP Test Email',
            message='This is a test email sent from the WorkTrack Pro diagnostic tool.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        print("\n✅ Success! The email was sent successfully.")
        print("Please check your inbox (and spam folder).")
    except Exception as e:
        print("\n❌ Failed to send email.")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        if "Authentication failed" in str(e) or "application-specific password" in str(e).lower():
            print("\n💡 TIP: It looks like an authentication issue.")
            print("If you are using Gmail, make sure you are using an 'App Password', not your regular Gmail password.")
            print("Instructions: https://support.google.com/accounts/answer/185833")
        elif "Connection refused" in str(e):
            print("\n💡 TIP: The connection was refused. Check your EMAIL_PORT (usually 587 for TLS) and EMAIL_USE_TLS settings.")

if __name__ == "__main__":
    test_smtp()
