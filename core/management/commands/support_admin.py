"""Create, restore or re-key the vendor support account (ROWD support): a super admin the vendor can always get back.

    manage.py support_admin --email support@rowd.tech                 # create (password printed once) or restore
    manage.py support_admin --email support@rowd.tech --reset-password  # new password, printed once
    WT_SUPPORT_PASSWORD=... manage.py support_admin --email ...         # use this password instead of a generated one

Restoring makes the account active, super admin, staff and superuser again, whatever was changed in the app, and
keeps its password unless --reset-password is given. Needs shell access to the server, so whoever runs the server can
always get back in. No password lives in the code: the repository is public. The account is a normal, visible user
(named "ROWD Support" by default), so the institution can see it in the user list.
"""
import os
import secrets

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Create or restore the vendor support super admin account.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Support account email (its sign-in name).')
        parser.add_argument('--name', default='ROWD Support', help='Display name (default: ROWD Support).')
        parser.add_argument('--reset-password', action='store_true', help='Set a new password (printed once).')

    def handle(self, *args, **opts):
        from users.models import CustomUser

        email = CustomUser.objects.normalize_email(opts['email'].strip())
        if '@' not in email:
            raise CommandError(f'"{email}" is not an email address.')
        first, _, last = opts['name'].strip().partition(' ')
        given = os.environ.get('WT_SUPPORT_PASSWORD', '').strip()
        if given and len(given) < 12:
            raise CommandError('WT_SUPPORT_PASSWORD must be at least 12 characters.')
        shown = None

        with transaction.atomic():
            user = CustomUser.objects.filter(email__iexact=email).first()
            if user is None:
                password = given or secrets.token_urlsafe(16)
                user = CustomUser.objects.create_superuser(email=email, password=password,
                                                           first_name=first, last_name=last)
                shown = None if given else password
                action = 'created'
            else:
                action = 'restored'
                if opts['reset_password'] or given:
                    password = given or secrets.token_urlsafe(16)
                    user.set_password(password)
                    shown = None if given else password
                    action += ', password reset'
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            if hasattr(user, 'role'):
                user.role = 'super_admin'
            if not user.first_name:
                user.first_name, user.last_name = first, last
            user.save()

        self.stdout.write(self.style.SUCCESS(f'Support account {email}: {action}.'))
        if shown:
            self.stdout.write(self.style.WARNING(f'Password for {email}: {shown}\nIt is shown once. Keep it in your password manager.'))
