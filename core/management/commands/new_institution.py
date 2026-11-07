"""Set up this install for an institution: identity, colours, language,
departments, roles (privilege profiles), sidebar visibility and the first
administrator.

    manage.py new_institution --config institution.json
    manage.py new_institution --name "University of X" --name-ar "جامعة س" \
        --brand "#7a1f2b" --accent "#f2b84b" --language ar \
        --admin-email admin@x.edu --admin-name "Amina Benali"

Flags override the file. See docs/institution.example.json for every key.
The whole run is one transaction: on any error nothing is saved. Re-running
is safe: departments and roles are matched by name and updated, an existing
admin keeps their password unless --reset-admin-password is given.
The ROWD credit is not configurable and is not touched here.
"""
import json
import re
import secrets
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

HEX = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')


def _hex(value, label):
    if value in (None, ''):
        return None
    value = str(value).strip()
    if not HEX.match(value):
        raise CommandError(f'{label}: "{value}" is not a hex colour such as #0033a0.')
    if len(value) == 4:
        value = '#' + ''.join(c * 2 for c in value[1:])
    return value.lower()


class Command(BaseCommand):
    help = 'Configure this install for an institution (name, logo, colours, language, departments, roles, first admin).'

    def add_arguments(self, parser):
        parser.add_argument('--config', help='JSON file (see docs/institution.example.json).')
        parser.add_argument('--name', help='Product name in English.')
        parser.add_argument('--name-ar', help='Product name in Arabic.')
        parser.add_argument('--logo', help='Path to a PNG/JPG/WebP logo.')
        parser.add_argument('--brand', help='Brand colour, e.g. #0033a0. Omit (with --accent) to keep the ROWD palette.')
        parser.add_argument('--accent', help='Accent colour.')
        parser.add_argument('--on-brand', help='Text colour on the brand colour (default: white or ink, whichever reads better).')
        parser.add_argument('--language', choices=['ar', 'en'], help='Default language.')
        parser.add_argument('--departments', help='Comma-separated department names.')
        parser.add_argument('--admin-email', help='First administrator email.')
        parser.add_argument('--admin-name', help='First administrator full name.')
        parser.add_argument('--admin-password', help='Password (default: a generated one, printed once).')
        parser.add_argument('--reset-admin-password', action='store_true', help='Set a new password if the admin already exists.')
        parser.add_argument('--dry-run', action='store_true', help='Validate and show what would change, then roll back.')

    # ── input ──────────────────────────────────────────────────────────────
    def _load(self, opts):
        cfg = {}
        if opts.get('config'):
            path = Path(opts['config'])
            if not path.is_file():
                raise CommandError(f'Config file not found: {path}')
            try:
                cfg = json.loads(path.read_text(encoding='utf-8'))
            except json.JSONDecodeError as e:
                raise CommandError(f'{path}: invalid JSON ({e}).')
            base = path.parent
            if cfg.get('logo') and not Path(cfg['logo']).is_absolute():
                cfg['logo'] = str(base / cfg['logo'])
        flag_map = {'name': 'name', 'name_ar': 'name_ar', 'logo': 'logo', 'brand': 'brand', 'accent': 'accent',
                    'on_brand': 'on_brand', 'language': 'language'}
        for opt, key in flag_map.items():
            if opts.get(opt):
                cfg[key] = opts[opt]
        if opts.get('departments'):
            cfg['departments'] = [d.strip() for d in opts['departments'].split(',') if d.strip()]
        admin = dict(cfg.get('admin') or {})
        if opts.get('admin_email'):
            admin['email'] = opts['admin_email']
        if opts.get('admin_name'):
            admin['name'] = opts['admin_name']
        if opts.get('admin_password'):
            admin['password'] = opts['admin_password']
        if admin:
            cfg['admin'] = admin
        return cfg

    def _validate(self, cfg):
        from users.models import SidebarVisibilityRule, SystemProfile

        if not (cfg.get('name') or '').strip():
            raise CommandError('A product name is required (--name or "name" in the config).')
        cfg['brand'] = _hex(cfg.get('brand'), 'brand')
        cfg['accent'] = _hex(cfg.get('accent'), 'accent')
        cfg['on_brand'] = _hex(cfg.get('on_brand'), 'on_brand')
        if bool(cfg['brand']) != bool(cfg['accent']):
            raise CommandError('Give both brand and accent, or neither (to keep the ROWD palette).')
        if cfg.get('language', 'ar') not in ('ar', 'en'):
            raise CommandError('language must be "ar" or "en".')
        if cfg.get('logo'):
            p = Path(cfg['logo'])
            if not p.is_file():
                raise CommandError(f'Logo not found: {p}')
            try:
                from PIL import Image
                with Image.open(p) as im:
                    im.verify()
            except Exception:
                raise CommandError(f'Logo is not a readable image: {p}')
        valid = {k for k, _ in SystemProfile.AVAILABLE_PRIVILEGES}
        for role in cfg.get('roles') or []:
            if not (role.get('name') or '').strip():
                raise CommandError('Every role needs a "name".')
            bad = set(role.get('privileges') or []) - valid
            if bad:
                raise CommandError(f'Role "{role["name"]}": unknown privileges {sorted(bad)}. Valid: {sorted(valid)}')
            role['color'] = _hex(role.get('color'), f'role {role["name"]} color')
        known = {k for k, *_ in self._sidebar_keys(SidebarVisibilityRule)}
        unknown = set(cfg.get('hide_sidebar') or []) - known
        if unknown:
            raise CommandError(f'hide_sidebar: unknown keys {sorted(unknown)}. Valid: {sorted(known)}')
        admin = cfg.get('admin') or {}
        if admin and not admin.get('email'):
            raise CommandError('admin.email is required when an admin is given.')
        return cfg

    @staticmethod
    def _sidebar_keys(model):
        if not model.objects.exists():
            model.initialize_defaults()
        return model.objects.values_list('feature_key')

    # ── apply ──────────────────────────────────────────────────────────────
    def handle(self, *args, **opts):
        cfg = self._validate(self._load(opts))
        out = []
        try:
            with transaction.atomic():
                out += self._site(cfg)
                out += self._departments(cfg)
                out += self._roles(cfg)
                out += self._sidebar(cfg)
                password_note = self._admin(cfg, opts, out)
                if opts['dry_run']:
                    raise _DryRun()
        except _DryRun:
            for line in out:
                self.stdout.write('  ' + line)
            self.stdout.write(self.style.WARNING('Dry run: nothing was saved.'))
            return
        for line in out:
            self.stdout.write('  ' + line)
        self.stdout.write(self.style.SUCCESS(f'Install configured for "{cfg["name"]}".'))
        if password_note:
            self.stdout.write(self.style.WARNING(password_note))

    def _site(self, cfg):
        from core.models import SiteConfiguration
        from users.models import SiteSettings

        c = SiteConfiguration.objects.first() or SiteConfiguration()
        c.app_name = cfg['name'].strip()
        c.app_name_ar = (cfg.get('name_ar') or cfg['name']).strip()
        lines = [f'Name: {c.app_name} / {c.app_name_ar}']
        if cfg['brand']:
            on = cfg['on_brand'] or _best_on(cfg['brand'])
            c.theme_preset = 'custom'
            c.primary_color, c.accent_color, c.on_brand_color = cfg['brand'], cfg['accent'], on
            lines.append(f'Colours: brand {cfg["brand"]}, accent {cfg["accent"]}, text on brand {on}')
        else:
            c.theme_preset = 'rowd'
            lines.append('Colours: ROWD palette')
        contact = cfg.get('contact') or {}
        for field, key in (('contact_email', 'email'), ('contact_phone', 'phone'), ('website_url', 'website'),
                           ('address', 'address'), ('address_ar', 'address_ar'),
                           ('footer_text', 'footer'), ('footer_text_ar', 'footer_ar')):
            if key in contact:
                setattr(c, field, (contact.get(key) or '').strip())
        if cfg.get('logo'):
            p = Path(cfg['logo'])
            with p.open('rb') as fh:
                c.logo.save(p.name, File(fh), save=False)
            lines.append(f'Logo: {p.name}')
        c.full_clean(exclude=['logo', 'gateway_image', 'background_image', 'banner_image'])
        c.save()

        s = SiteSettings.get_settings()
        s.default_language = cfg.get('language', 'ar')
        if 'allow_registration' in cfg:
            s.allow_registration = bool(cfg['allow_registration'])
        s.save()
        lines.append(f'Default language: {s.default_language}; account requests {"on" if s.allow_registration else "off"}')
        return lines

    def _departments(self, cfg):
        from users.models import Department

        items = cfg.get('departments') or []
        made = 0
        for item in items:
            if isinstance(item, str):
                item = {'name': item}
            name = (item.get('name') or '').strip()
            if not name:
                continue
            d, created = Department.objects.get_or_create(name=name, defaults={'description': item.get('description', '')})
            if not created and 'description' in item:
                d.description = item['description']
                d.save()
            made += created
        return [f'Departments: {len(items)} given, {made} new'] if items else []

    def _roles(self, cfg):
        from users.models import SystemProfile

        roles = cfg.get('roles') or []
        made = 0
        for r in roles:
            obj, created = SystemProfile.objects.get_or_create(name=r['name'].strip())
            obj.name_ar = (r.get('name_ar') or obj.name_ar or '').strip()
            obj.description = r.get('description', obj.description)
            obj.privileges = list(r.get('privileges') or [])
            if r.get('color'):
                obj.color = r['color']
            obj.save()
            made += created
        return [f'Roles: {len(roles)} given, {made} new'] if roles else []

    def _sidebar(self, cfg):
        from users.models import SidebarVisibilityRule

        hide = cfg.get('hide_sidebar')
        if hide is None:
            return []
        SidebarVisibilityRule.objects.filter(feature_key__in=hide).update(is_allowed=False)
        SidebarVisibilityRule.objects.exclude(feature_key__in=hide).filter(is_allowed=False).update(is_allowed=True)
        return [f'Sidebar hidden: {", ".join(hide) or "nothing"}']

    def _admin(self, cfg, opts, out):
        from users.models import CustomUser

        admin = cfg.get('admin')
        if not admin:
            out.append('Admin: none given (add one with --admin-email)')
            return None
        email = CustomUser.objects.normalize_email(admin['email'].strip())
        first, _, last = (admin.get('name') or '').strip().partition(' ')
        user = CustomUser.objects.filter(email__iexact=email).first()
        password = admin.get('password')
        note = None
        if user is None:
            if not password:
                password = secrets.token_urlsafe(12)
                note = f'Admin password for {email}: {password}\nIt is shown once. Ask the admin to change it after signing in.'
            user = CustomUser.objects.create_superuser(email=email, password=password, first_name=first, last_name=last)
            out.append(f'Admin: created {email}')
        else:
            user.role = 'super_admin'
            user.is_staff = user.is_superuser = user.is_active = True
            if first:
                user.first_name, user.last_name = first, last
            if opts.get('reset_admin_password'):
                if not password:
                    password = secrets.token_urlsafe(12)
                    note = f'New admin password for {email}: {password}\nIt is shown once.'
                user.set_password(password)
            user.save()
            out.append(f'Admin: {email} already existed, made super admin' + (', password reset' if opts.get('reset_admin_password') else ''))
        if cfg.get('admin_department'):
            from users.models import Department
            user.department = Department.objects.filter(name=cfg['admin_department']).first()
            user.save(update_fields=['department'])
        return note


class _DryRun(Exception):
    pass


def _best_on(brand):
    """White or ink, whichever reads better on the brand colour (WCAG contrast)."""
    def lum(h):
        n = int(h[1:], 16)
        ch = []
        for c in ((n >> 16) & 255, (n >> 8) & 255, n & 255):
            c /= 255
            ch.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]

    def ratio(a, b):
        la, lb = lum(a), lum(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

    return '#ffffff' if ratio('#ffffff', brand) >= ratio('#131925', brand) else '#131925'
