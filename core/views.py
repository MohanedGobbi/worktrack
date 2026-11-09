import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import rotate_token
from django.contrib import messages
from django.conf import settings as dj_settings
from .models import SiteConfiguration, AllowedHost, BlockedHostAttempt
from .forms import SiteConfigurationForm, SiteThemeForm

logger = logging.getLogger('django.security.csrf')


def csrf_failure_view(request, reason=""):
    """
    Intelligent CSRF failure recovery.
    Instead of an unhelpful 403 aborted page, automatically rotate/refresh the CSRF
    token and redirect users back with a clear notification so their flow is never blocked.
    """
    logger.warning(f"CSRF verification failed: {reason} on path {request.path}")
    
    # 1. Login & Registration flow: refresh CSRF cookie and redirect back to login
    clean_path = request.path.rstrip('/')
    if clean_path.endswith(('login', 'register')):
        dest = request.get_full_path()
        response = redirect(dest)
        rotate_token(request)
        messages.warning(request, "Your security session was refreshed. Please enter your credentials to continue.")
        return response

    # 2. Site settings flow: refresh token and redirect back to site settings
    if 'site-settings' in request.path:
        response = redirect('site-settings')
        rotate_token(request)
        messages.warning(request, "Your session token was updated. Please re-apply your changes.")
        return response

    # 3. For any other page, provide a polished recovery page with a 1-click retry
    response = render(request, '403_csrf.html', {
        'reason': reason,
        'path': request.path,
    }, status=403)
    rotate_token(request)
    return response


def is_super_admin(user):
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'super_admin'

@login_required
@user_passes_test(is_super_admin)
@ensure_csrf_cookie
def site_settings_view(request):
    """Site Settings: identity, theme colours, contact/footer, language and access."""
    from users.models import SiteSettings
    from core.context_processors import WT_SWATCHES, _wt_lang
    ar = _wt_lang(request) == 'ar'

    config = SiteConfiguration.objects.first() or SiteConfiguration.objects.create()
    site = SiteSettings.get_settings()

    if request.method == 'POST':
        form = SiteThemeForm(request.POST, request.FILES, instance=config)
        lang = request.POST.get('default_language')
        if form.is_valid() and lang in ('ar', 'en'):
            obj = form.save(commit=False)
            if request.POST.get('logo-clear') and not request.FILES.get('logo'):
                obj.logo = None
            if request.POST.get('banner_image-clear') and not request.FILES.get('banner_image'):
                obj.banner_image = None
            if request.POST.get('partner_logo-clear') and not request.FILES.get('partner_logo'):
                obj.partner_logo = None
            obj.save()
            site.default_language = lang
            site.allow_registration = request.POST.get('allow_registration') == 'on'
            site.save()
            messages.success(request, 'تم حفظ إعدادات الموقع.' if ar else 'Site settings saved.')
            return redirect('site-settings')
        if lang not in ('ar', 'en'):
            form.add_error(None, 'اختر اللغة الافتراضية.' if ar else 'Choose the default language.')
        messages.error(request, 'يرجى مراجعة الحقول المحددة.' if ar else 'Please check the highlighted fields.')
        # is_valid() copied the posted values onto `config`; render the page around the saved row instead.
        config = SiteConfiguration.objects.get(pk=config.pk)
    else:
        form = SiteThemeForm(instance=config)

    # Colours the inputs start from: the saved custom colours, or the preset in use.
    from core.context_processors import THEME_PRESET_COLORS
    preset = config.theme_preset or 'rowd'
    if request.method == 'POST':
        start = {'brand': request.POST.get('primary_color', ''), 'accent': request.POST.get('accent_color', ''),
                 'on_brand': request.POST.get('on_brand_color', '')}
    elif preset == 'custom':
        start = {'brand': config.primary_color, 'accent': config.accent_color, 'on_brand': config.on_brand_color}
    else:
        p = THEME_PRESET_COLORS.get(preset, THEME_PRESET_COLORS['rowd'])
        start = {'brand': p['primary'], 'accent': p['accent'], 'on_brand': '#ffffff'}

    return render(request, 'pages/site_settings.html', {
        'form': form,
        'site_flags': site,
        'ss_mode': form['theme_preset'].value() or 'rowd',
        'ss_start': start,
        'ss_swatches': WT_SWATCHES,
        'wt_demo': getattr(dj_settings, 'DEMO_MODE', False),
        'ss_lang': request.POST.get('default_language') or site.default_language,
        'ss_allow_registration': (request.POST.get('allow_registration') == 'on') if request.method == 'POST' else site.allow_registration,
    })


@login_required
@user_passes_test(is_super_admin)
def host_management_view(request):
    """View to manage authorized hosts and review blocked intrusion attempts."""
    
    if request.method == 'POST':
        # Quick-add a new host manually
        new_hostname = request.POST.get('hostname', '').strip().lower()
        description = request.POST.get('description', 'Added via Admin Dashboard')
        if new_hostname:
            obj, created = AllowedHost.objects.get_or_create(
                hostname=new_hostname,
                defaults={'description': description}
            )
            if not created and not obj.is_active:
                # Re-enable if it existed but was disabled
                obj.is_active = True
                obj.save()
            if new_hostname == '*':
                from django.core.cache import cache
                cache.delete('allowed_host_wildcard')
                messages.success(request, "⚠️ OPEN MODE enabled — all hosts and IPs are now accepted.")
            else:
                messages.success(request, f"Host '{new_hostname}' successfully added to whitelist.")
        return redirect('host-management')
        
    allowed_hosts = AllowedHost.objects.all().order_by('-id')
    blocked_attempts = BlockedHostAttempt.objects.all().order_by('-last_attempt')[:50]

    wildcard_host = AllowedHost.objects.filter(hostname='*').first()
    wildcard_active = wildcard_host is not None and wildcard_host.is_active
    
    return render(request, 'pages/host_management.html', {
        'allowed_hosts': allowed_hosts,
        'blocked_attempts': blocked_attempts,
        'wildcard_active': wildcard_active,
        'wildcard_host': wildcard_host,
    })


@login_required
@user_passes_test(is_super_admin)
def whitelist_host_action(request, attempt_id):
    """Quickly convert a blocked intrusion attempt into an AllowedHost, allowing both the domain and the IP."""
    if request.method == 'POST':
        attempt = get_object_or_404(BlockedHostAttempt, id=attempt_id)
        
        # Whitelist the requested hostname (usually domain)
        AllowedHost.objects.get_or_create(
            hostname=attempt.hostname,
            defaults={'description': f'Auto-whitelisted domain (IP: {attempt.ip_address})'}
        )
        
        # Also whitelist the client IP address to fully unblock the user on a network layer
        if attempt.ip_address and attempt.ip_address != attempt.hostname:
            AllowedHost.objects.get_or_create(
                hostname=attempt.ip_address,
                defaults={'description': f'Auto-whitelisted IP (from domain: {attempt.hostname})'}
            )

        # Clear out any other stored attempts originating from this same IP
        if attempt.ip_address:
             BlockedHostAttempt.objects.filter(ip_address=attempt.ip_address).delete()
        else:
             attempt.delete()
             
        messages.success(request, f"Successfully whitelisted '{attempt.hostname}' and its IP.")
    return redirect('host-management')


@login_required
@user_passes_test(is_super_admin)
def toggle_host_status(request, host_id):
    if request.method == 'POST':
        from django.core.cache import cache
        host = get_object_or_404(AllowedHost, id=host_id)
        host.is_active = not host.is_active
        host.save()
        # Clear wildcard cache to immediately reflect the change
        if host.hostname == '*':
            cache.delete('allowed_host_wildcard')
        else:
            cache.delete(f'allowed_host_{host.hostname}')
        status = "enabled" if host.is_active else "disabled"
        messages.success(request, f"Host '{host.hostname}' is now {status}.")
    return redirect('host-management')


@login_required
@user_passes_test(is_super_admin)
def delete_host_action(request, host_id):
    if request.method == 'POST':
        host = get_object_or_404(AllowedHost, id=host_id)
        hostname = host.hostname
        host.delete()
        messages.success(request, f"Host '{hostname}' was removed from the whitelist.")
    return redirect('host-management')


import os
import uuid
from django.core.files.storage import default_storage


# ─────────────────────────────────────────────────────────────────────────────
# Health check and automatic updates (see deploy/linux and docs/guides/INSTALL_LINUX.md)
# The web app never runs anything as root: it only reads the updater's status file and drops a request file that a
# systemd .path unit turns into an updater run.
# ─────────────────────────────────────────────────────────────────────────────
from pathlib import Path as _Path

_UPDATE_STATES = {'checking', 'up_to_date', 'downloading', 'installing', 'updated', 'failed', 'skipped', 'error'}
_UPDATE_REQUEST_NAME = 'request'


def healthz(request):
    """Liveness for the updater and load balancers: the app answers and the database responds."""
    from django.db import connection
    from worktrack_pro.version import get_version
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        return JsonResponse({'status': 'error'}, status=503)
    return JsonResponse({'status': 'ok', 'version': get_version()})


def _read_update_status():
    """The updater's last report, or {} when missing, unreadable or not a known state."""
    from django.conf import settings
    try:
        data = json.loads(_Path(settings.UPDATE_STATUS_FILE).read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(data, dict) or data.get('state') not in _UPDATE_STATES:
        return {}
    return {k: str(data.get(k) or '') for k in ('state', 'installed', 'latest', 'message', 'timestamp')}


def _update_paths():
    from django.conf import settings
    folder = _Path(settings.UPDATE_REQUEST_DIR)
    return folder, folder / _UPDATE_REQUEST_NAME


def _admin_json_guard(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Sign in first.'}, status=401)
    if getattr(request.user, 'role', '') != 'super_admin':
        return JsonResponse({'status': 'error', 'message': 'Administrators only.'}, status=403)
    return None


def update_status(request):
    """GET: installed version, whether updates are set up, whether a check is pending, and the last report."""
    from worktrack_pro.version import version_info
    bounce = _admin_json_guard(request)
    if bounce:
        return bounce
    folder, req = _update_paths()
    info = version_info()
    return JsonResponse({
        'installed': info['version'], 'commit': info['commit'], 'build_date': info['build_date'],
        'configured': folder.is_dir(), 'pending': req.exists(), 'status': _read_update_status(),
    })


def update_check(request):
    """POST (password again): ask the server to look for a new release now."""
    from django.conf import settings
    from django.utils import timezone
    bounce = _admin_json_guard(request)
    if bounce:
        return bounce
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST only.'}, status=405)
    if getattr(settings, 'DEMO_MODE', False):
        return JsonResponse({'status': 'error', 'code': 'demo', 'message': 'Not available in demo mode.'}, status=403)
    if not request.user.check_password(request.POST.get('password') or ''):
        return JsonResponse({'status': 'error', 'code': 'password', 'message': 'Wrong password.'}, status=403)
    folder, req = _update_paths()
    if not folder.is_dir():
        return JsonResponse({'status': 'error', 'code': 'not_configured', 'message': 'Automatic updates are not set up on this server.'}, status=409)
    try:
        tmp = folder / f'.{_UPDATE_REQUEST_NAME}.tmp'
        tmp.write_text(json.dumps({'by': request.user.email, 'at': timezone.now().isoformat()}), encoding='utf-8')
        tmp.replace(req)
    except OSError:
        return JsonResponse({'status': 'error', 'code': 'write', 'message': 'Could not write the request file.'}, status=500)
    try:
        from audit.models import ActivityLog
        ActivityLog.objects.create(user=request.user, action='update', object_type='Software', object_id=0,
                                   object_str='Update check', description='Asked the server to check for a new release',
                                   ip_address=request.META.get('REMOTE_ADDR'))
    except Exception:
        logger.warning('Could not record the update request in the activity log', exc_info=True)
    return JsonResponse({'status': 'requested'})
