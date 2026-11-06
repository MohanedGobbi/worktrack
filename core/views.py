import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import rotate_token
from django.contrib import messages
from .models import SiteConfiguration, AllowedHost, BlockedHostAttempt
from .forms import SiteConfigurationForm

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
    """View for updating site-wide settings."""
    config = SiteConfiguration.objects.first()
    if not config:
        config = SiteConfiguration.objects.create()

    if request.method == 'POST':
        form = SiteConfigurationForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Site settings updated successfully!")
            return redirect('site-settings')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SiteConfigurationForm(instance=config)

    return render(request, 'pages/site_settings.html', {
        'form': form,
        'site_config': config,
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
